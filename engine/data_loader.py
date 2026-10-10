"""Read-only repository. Published rows remain separate; all used fields are gated.

Schema definitions are shared with the existing pipeline, but no builder is run.
Source-file and evidence-text hashes are checked against the inspection ledger.
"""
import csv
import hashlib
import math
from pathlib import Path
from scripts.common import SCHEMAS, CATEGORIES, TECHNOLOGIES
from .food_reference import FOOD_SUBTYPE, FOOD_PARAMETER_IDS

ROOT = Path(__file__).resolve().parents[1]

class DataError(ValueError):
    pass

class DataRepository:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.tables = {}
        self.hashes = {}
        self.issues = []
        self._hash_cache = {}
        for name, required in SCHEMAS.items():
            path = self.root / 'data' / f'{name}.csv'
            self.hashes[name] = self._hash(path)
            with path.open(encoding='utf-8-sig', newline='') as handle:
                reader = csv.DictReader(handle)
                if not set(required).issubset(reader.fieldnames or []):
                    raise DataError(f'{name}: missing required columns')
                if len(reader.fieldnames) != len(set(reader.fieldnames)):
                    raise DataError(f'{name}: duplicate columns')
                self.tables[name] = list(reader)
        self.sources = self._index('sources', 'source_id')
        self._index('waste_properties', 'waste_id')
        self._index('conversion_parameters', 'parameter_id')
        self._index('technology_mapping', 'record_id')
        self._index('technology_performance', 'record_id')
        self.ledger = {}
        for row in self.tables['source_verification']:
            key = (row.get('dataset_name'), row.get('record_id'), row.get('field_name'))
            self.ledger.setdefault(key, []).append(row)
        self.validate()

    def _index(self, table, key):
        result = {}
        for row in self.tables[table]:
            if not row[key] or row[key] in result:
                raise DataError(f'{table}: missing or duplicate {key}')
            result[row[key]] = row
        return result

    def _hash(self, path):
        path = Path(path)
        if path not in self._hash_cache:
            self._hash_cache[path] = hashlib.sha256(path.read_bytes()).hexdigest()
        return self._hash_cache[path]

    def _local_file(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise DataError('Evidence path leaves project')
        return path

    def source_is_verified(self, source_id):
        source = self.sources.get(source_id, {})
        if source.get('verification_status') != 'verified' or source.get('retrieval_status') != 'downloaded':
            return False
        try:
            path = self._local_file(source['dataset_filename'])
            return bool(source.get('sha256')) and self._hash(path) == source['sha256']
        except (OSError, KeyError, DataError):
            return False

    def evidence_for(self, table, row, field):
        return [dict(e) for e in self.ledger.get((table, row.get('record_id', row.get('waste_id')), field), [])]

    def verified_field(self, table, row, field):
        value = row.get(field)
        if value in ('', None) or row.get('verification_status') != 'verified' or not self.source_is_verified(row['source_id']):
            return False
        for evidence in self.evidence_for(table, row, field):
            if evidence['verification_status'] != 'verified' or evidence['retrieval_status'] != 'downloaded' or evidence['source_id'] != row['source_id']:
                continue
            try:
                path = self._local_file(evidence['evidence_file'])
                if not evidence.get('evidence_location') or self._hash(path) != evidence.get('evidence_sha256'):
                    continue
                if evidence.get('raw_sha256') != self.sources[row['source_id']].get('sha256'):
                    continue
                if table == 'conversion_parameters' and evidence.get('measurement_basis') != row.get('measurement_basis'):
                    continue
                if table == 'conversion_parameters' and evidence.get('converted_unit') != row.get('unit'):
                    continue
                if table == 'waste_properties' and field in ('hhv_mj_kg', 'lhv_mj_kg') and evidence.get('measurement_basis') != row.get('heating_value_basis'):
                    continue
                if field == 'mapping_evidence':
                    if value == evidence['converted_value']:
                        return True
                elif math.isclose(float(value), float(evidence['converted_value']), rel_tol=1e-10, abs_tol=1e-10):
                    return True
            except (OSError, ValueError, KeyError, DataError):
                continue
        return False

    def validate(self):
        self.issues = []
        for table, rows in self.tables.items():
            if table in ('sources', 'source_verification'):
                continue
            for row in rows:
                if row['source_id'] not in self.sources:
                    raise DataError(f'{table}: unknown source {row["source_id"]}')
                if table == 'waste_properties':
                    if row['waste_category'] not in CATEGORIES:
                        raise DataError('Unknown waste category')
                    for key, value in row.items():
                        if value and ('_pct' in key or key in ('hhv_mj_kg', 'lhv_mj_kg')):
                            number = self.numeric(value)
                            if number < 0 or ('_pct' in key and number > 100):
                                raise DataError(f'{row["waste_id"]}: invalid {key}')
                    if row.get('model_ready') == 'false':
                        self.issues.append(f'{row["waste_id"]}: excluded from calculations: {row.get("quality_flag")}')
                    if row.get('moisture_pct') and row.get('total_solids_pct') and abs(float(row['moisture_pct']) + float(row['total_solids_pct']) - 100) > .05:
                        raise DataError('Moisture/total-solids basis inconsistency')
                elif table == 'conversion_parameters':
                    if row['technology'] not in TECHNOLOGIES or not row['unit'] or not row['measurement_basis']:
                        raise DataError('Parameter lacks technology/unit/basis')
                    values = [self.numeric(row[k]) for k in ('value_min', 'value_typical', 'value_max') if row[k]]
                    if values != sorted(values) or any(v < 0 for v in values) and row['unit'] != 'degC':
                        raise DataError(f'{row["parameter_id"]}: invalid range')
                    if row['unit'].startswith('%') and any(v > 100 for v in values):
                        raise DataError(f'{row["parameter_id"]}: percentage exceeds physical bound')
                elif table == 'technology_performance':
                    for field in ('capacity', 'nominal_capacity', 'auxiliary_energy_consumption', 'operating_temperature_c'):
                        if row.get(field):
                            value = self.numeric(row[field])
                            if field != 'operating_temperature_c' and value < 0:
                                raise DataError(f'Invalid equipment {field}')
                    for field in ('electrical_efficiency_pct', 'thermal_efficiency_pct'):
                        if row[field] and not 0 <= self.numeric(row[field]) <= 100:
                            raise DataError('Invalid equipment efficiency')
                    if row['capacity'] and not row.get('capacity_unit'):
                        raise DataError('Equipment capacity lacks unit')

    @staticmethod
    def numeric(value):
        try:
            result = float(value)
        except (ValueError, TypeError):
            raise DataError(f'Invalid numeric value: {value}') from None
        if not math.isfinite(result):
            raise DataError('Nonfinite dataset number')
        return result

    def waste_properties(self, category, subtype, property_id=None):
        return [dict(r) for r in self.tables['waste_properties'] if r['waste_category'].casefold() == category.casefold() and r['waste_subtype'].casefold() == subtype.casefold() and (property_id is None or r['waste_id'] == property_id)]

    def conversion_parameters(self, technology, subtype=None):
        if technology == 'Anaerobic digestion' and subtype == FOOD_SUBTYPE:
            return [dict(r) for r in self.tables['conversion_parameters']
                    if r['technology'] == technology and r['parameter_id'] in FOOD_PARAMETER_IDS
                    and r['waste_subtype'] == 'EBMUD food waste pulp' and r['source_id'] == 'S03']
        return [dict(r) for r in self.tables['conversion_parameters'] if r['technology'] == technology and (subtype is None or r['waste_subtype'].casefold() == subtype.casefold())]

    def equipment_performance(self, technology):
        return [dict(r) for r in self.tables['technology_performance'] if r['technology_name'] == technology]

    def source(self, source_id):
        return dict(self.sources[source_id])

    def applicable_technologies(self, category, subtype):
        # Explicit scopes only. No category-wide or fuzzy transfer of evidence.
        aliases = {
            # Explicit documented digestion -> biogas -> CHP chains. CHP remains
            # blocked until fuel qualification and equipment/scale are established.
            'Source-separated food waste': {'M0001', 'M0007'},
            'Animal manures': {'M0002', 'M0008'},
            'Wastewater solids': {'M0003', 'M0009'},
            'Dry wood reference': {'M0013'},
            'EBMUD food waste pulp': {'M0001', 'M0007'},
            FOOD_SUBTYPE: {'M0001', 'M0007'},
            'EBMUD source-separated delivered food waste': {'M0001', 'M0007'},
            'EBMUD municipal wastewater solids': {'M0003', 'M0009'},
            'Detroit 50/50 primary/secondary sludge; WW06 SS-2': {'M0024'},
        }
        ids = set(aliases.get(subtype, set()))
        # Published samples within the documented animal-manure scope acquire
        # qualitative applicability only, never an inferred methane yield.
        if self.waste_properties(category, subtype) and category == 'Animal manure':
            ids.update({'M0002', 'M0008'})
        if any(r['waste_subtype'] == subtype and r['technology'] == 'Gasification' and r['source_id'] == 'S02' and 'Walawender 1985 run ' in subtype for r in self.tables['conversion_parameters']):
            ids.add('M0012')
        # Exact published garbage samples are reference MSW, conditional on exclusion
        # of hazardous/recyclable fractions; actual composition is not assumed.
        if any(r['waste_subtype'] == subtype and 'Dry shredded garbage' in subtype for r in self.tables['waste_properties']):
            ids.add('M0019')
        rows = []
        for r in self.tables['technology_mapping']:
            if r['waste_category'].casefold() != category.casefold():
                continue
            if r['waste_subtype'].casefold() == subtype.casefold() or r['record_id'] in ids:
                if self.verified_field('technology_mapping', r, 'mapping_evidence'):
                    rows.append(dict(r))
        return rows

    def unchanged(self):
        return all(hashlib.sha256((self.root/'data'/f'{name}.csv').read_bytes()).hexdigest() == digest for name, digest in self.hashes.items())
