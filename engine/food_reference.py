"""One explicit join of existing S03 records, not a new scientific dataset.

Only the mesophilic 15-day reference pulp is in scope. Published averages
are joined by exact experimental condition; pooled methane yields are excluded.
"""
FOOD_SUBTYPE = 'EBMUD food waste pulp; mesophilic; 15-day MCRT'
FOOD_PARAMETER_IDS = {'P0006', 'P0007', 'P0009'}
FIELDS = {
    'gas_rate': ('conversion_parameters', 'P0006', ('value_typical',)),
    'methane_fraction': ('conversion_parameters', 'P0007', ('value_typical',)),
    'vs_loading': ('conversion_parameters', 'P0009', ('value_typical',)),
    'sample': ('waste_properties', 'W0059', ('total_solids_pct', 'volatile_solids_pct_ts')),
    'reactor': ('technology_performance', 'T0012', ('capacity', 'operating_temperature_c')),
}


def food_bundle(repo):
    rows, missing = {}, []
    for name, (table, identifier, fields) in FIELDS.items():
        matches = [r for r in repo.tables[table] if r['record_id'] == identifier]
        if len(matches) != 1 or matches[0]['source_id'] != 'S03':
            missing.append(f'Exact S03 {table} record {identifier}')
            continue
        row = rows[name] = matches[0]
        for field in fields:
            if not repo.verified_field(table, row, field):
                missing.append(f'Verified {identifier}.{field} with intact original evidence')
    if len(rows) != len(FIELDS):
        return rows, missing
    conditions = '30 L bench digester; mesophilic; 15-day MCRT; food waste pulp'
    if any(rows[k]['technology'] != 'Anaerobic digestion' or
           rows[k]['waste_subtype'] != 'EBMUD food waste pulp' or
           rows[k]['operating_conditions'] != conditions
           for k in ('gas_rate', 'methane_fraction', 'vs_loading')):
        missing.append('Matching mesophilic 15-day S03 operating conditions; no pooled-study transfer')
    expected = [('gas_rate', 'unit', 'L biogas/h'),
                ('gas_rate', 'measurement_basis', 'total gas volume per reactor time; reference T/P unspecified'),
                ('vs_loading', 'unit', 'lb VS/ft3/day'),
                ('vs_loading', 'measurement_basis', 'volatile solids feed per reactor volume per day'),
                ('methane_fraction', 'unit', '%'),
                ('methane_fraction', 'measurement_basis', 'volume fraction CH4 in biogas'),
                ('sample', 'waste_subtype', FOOD_SUBTYPE),
                ('sample', 'waste_category', 'Food and organic waste'),
                ('sample', 'solids_basis', 'TS % wet feed; VS % TS'),
                ('reactor', 'capacity_unit', 'L reactor volume'),
                ('reactor', 'equipment_type', 'EBMUD mesophilic acrylic bench digester')]
    if any(rows[name].get(field) != value for name, field, value in expected):
        missing.append('Compatible exact food sample, gas species and wet/TS/VS/reactor-volume bases')
    if rows['sample'].get('model_ready') == 'false':
        missing.append('Model-ready exact published reference sample')
    return rows, missing


def linked_food_parameters(repo):
    rows, missing = food_bundle(repo)
    if missing:
        return []
    return [dict(record_id=rows[name]['record_id'], field=field,
                 value=rows[name][field], unit=rows[name].get('unit',
                 '% wet feed' if field == 'total_solids_pct' else '% of TS' if field == 'volatile_solids_pct_ts' else 'L reactor volume' if field == 'capacity' else 'degC target'),
                 source_id='S03', evidence_location=rows[name]['evidence_location'])
            for name, (_, _, fields) in FIELDS.items() for field in fields]
