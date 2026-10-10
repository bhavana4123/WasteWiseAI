from dataclasses import asdict
from ..models import CalculationResult
from ..units import dry_mass
from ..numerics import finite, checked_product, validate_numeric_tree, NumericalError

def base(request, technology, mapping):
    details = asdict(request)
    details['mass_kg'] = request.mass_kg
    result = CalculationResult(details, technology, energy_output_type=request.desired_output)
    if mapping:
        result.feasibility_status = mapping['feasibility_status']
        result.source_ids.append(mapping['source_id'])
        result.limitations.extend(filter(None, [mapping['required_conditions'], mapping['preprocessing_required'], mapping['limitations'], mapping.get('regulatory_restrictions')]))
        result.evidence.append({'dataset': 'technology_mapping', 'record_id': mapping['record_id'], 'field': 'mapping_evidence', 'evidence_location': mapping.get('evidence_location')})
    else:
        result.feasibility_status = 'not_established'
        result.calculation_status = 'NOT_APPLICABLE'
        result.missing_parameters.append('Verified feedstock-to-technology mapping')
    if mapping and (mapping.get('hazard_flag') == 'true' or mapping['feasibility_status'] == 'restricted'):
        result.feasibility_status = 'restricted'
        result.calculation_status = 'RESTRICTED'
        result.warnings.append('Hazardous/regulated material: no conversion calculation or recommendation; specialist permitting and contaminant assessment required.')
    return result

def add_parameter(repo, result, table, row, field, unit):
    if not repo.verified_field(table, row, field):
        result.missing_parameters.append(f'Verified {row.get("record_id")}.{field} with intact original evidence')
        return None
    value = finite(float(row[field]), f'Parameter {row.get("record_id")}.{field}')
    result.parameters.append({'record_id': row['record_id'], 'name': row.get('parameter_name', field), 'field': field, 'value': value, 'unit': unit, 'measurement_basis': row.get('measurement_basis', row.get('heating_value_basis')), 'operating_conditions': row.get('operating_conditions', ''), 'source_id': row['source_id']})
    if row['source_id'] not in result.source_ids:
        result.source_ids.append(row['source_id'])
    for e in repo.evidence_for(table, row, field):
        result.evidence.append({k: e.get(k) for k in ('record_id', 'field_name', 'source_id', 'evidence_location', 'evidence_file', 'conversion_formula', 'original_value', 'original_unit', 'converted_value', 'converted_unit')})
    if row.get('limitations') and row['limitations'] not in result.limitations:
        result.limitations.append(row['limitations'])
    return value

def feed_dry_mass(repo, request, result):
    if request.moisture_pct is not None:
        result.assumptions.append('User moisture is wet-basis mass percent; user feed characterization is not source-verified.')
        result.parameters.append({'name': 'moisture_pct', 'value': float(request.moisture_pct), 'unit': '% wet mass', 'origin': 'user'})
        result.uncertainty['moisture_sensitivity'] = 'Holding reference yield constant, dry-mass accounting changes by -1/(100-moisture_pct) of its value per percentage-point moisture increase, away from 100%. This is not a process moisture-response model.'
        return dry_mass(request.mass_kg, request.moisture_pct)
    properties = repo.waste_properties(request.waste_category, request.waste_subtype, request.property_id)
    if len(properties) == 1 and properties[0].get('model_ready') != 'false':
        row = properties[0]
        if row.get('moisture_pct'):
            value = add_parameter(repo, result, 'waste_properties', row, 'moisture_pct', '% wet mass')
            if value is not None:
                result.assumptions.append('Input is the exact published sample at its reported moisture; not representative of arbitrary waste.')
                return dry_mass(request.mass_kg, value)
        elif row.get('total_solids_pct') and 'wet' in row.get('solids_basis', '').lower():
            value = add_parameter(repo, result, 'waste_properties', row, 'total_solids_pct', '% wet mass')
            if value is not None:
                return checked_product(request.mass_kg, value / 100, operation='Total-solids feed mass')
    result.missing_parameters.append('Wet-basis moisture or verified same-sample total solids (no default)')
    return None

def selected_parameter(repo, request, result, technology, names):
    rows = [r for r in repo.conversion_parameters(technology, request.waste_subtype) if r['parameter_name'] in names]
    if request.parameter_id:
        rows = [r for r in rows if r['parameter_id'] == request.parameter_id]
    if len(rows) != 1:
        result.missing_parameters.append('Explicit applicable parameter_id / operating-study selection' if rows else 'Verified feedstock-specific yield with suitable mass basis')
        result.uncertainty['available_parameter_ids'] = [r['parameter_id'] for r in rows]
        return None
    result.scenario_id = rows[0]['parameter_id']
    return rows[0]

def reference_gate(request, result):
    if not request.reference_mode:
        result.missing_parameters.append('Equipment-specific feedstock validation, capacity, operating duration and scale applicability; use reference_mode only for published reference scenarios')
        return False
    result.assumptions.append('Published reference scenario only; linear mass accounting under the stated study conditions, not equipment sizing or a plant forecast.')
    result.warnings.append('Feed equivalence, preprocessing, reactor conditions and scale have not been established for an operating installation.')
    return True

def product_success(result, value, unit, formula, classification='intermediate_product_quantity'):
    finite(value, 'Primary calculated quantity')
    if value < 0:
        raise NumericalError('NEGATIVE_QUANTITY', 'Primary calculated quantity')
    if result.missing_parameters:
        return result
    result.calculated_value = value
    result.unit = unit
    result.formula = formula
    result.gross_vs_net_classification = classification
    result.calculation_status = 'CALCULATED_REFERENCE'
    result.uncertainty.setdefault('statistical', 'No confidence interval provided; reference yields are not uncertainty bounds.')
    return result

def numeric_failure(result, error):
    """Discard incomplete outputs; do not retain an invalid partial energy total."""
    result.calculation_status = 'INSUFFICIENT_DATA'
    result.calculated_value = None
    result.unit = None
    result.gross_vs_net_classification = 'not_calculated'
    result.intermediate_products = []
    result.errors.append({'code': error.code, 'operation': error.operation, 'message': str(error)})
    result.missing_parameters.append(f'Finite representable numerical result for {error.operation}')
    result.warnings.append('Numerical failure blocks this calculation and recommendation; no infinity, NaN or invented zero is returned.')
    # Defensive final sanitization protects the structured error even if an
    # auxiliary range or future module had already inserted a non-finite number.
    def sanitize(value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                return finite(value, 'Error response')
            except NumericalError:
                return None
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        if isinstance(value, dict):
            return {key: sanitize(item) for key, item in value.items()}
        return value
    result.parameters = sanitize(result.parameters)
    result.input_waste_details = sanitize(result.input_waste_details)
    result.uncertainty = sanitize(result.uncertainty)
    result.feasibility_checks = sanitize(result.feasibility_checks)
    result.evidence = sanitize(result.evidence)
    return result

def finalize_result(result):
    validate_numeric_tree(result.to_dict())
    for parameter in result.parameters:
        if parameter.get('value') is not None:
            finite(parameter['value'], 'Parameter value')
    if result.calculation_status == 'CALCULATED_REFERENCE' and result.calculated_value is None:
        raise NumericalError('MISSING_CALCULATED_VALUE', 'Primary calculated quantity')
    if result.calculated_value is not None:
        finite(result.calculated_value, 'Primary calculated quantity')
        if result.calculated_value < 0:
            raise NumericalError('NEGATIVE_QUANTITY', 'Primary calculated quantity')
    for product in result.intermediate_products:
        if product.get('value') is not None:
            finite(product['value'], 'Intermediate product')
            if product['value'] < 0:
                raise NumericalError('NEGATIVE_QUANTITY', 'Intermediate product')
    return result
