"""Rate-based reconstruction for one exact EBMUD reference condition.

This does not turn a reactor L/h observation into a reported mass yield.
The ratio of matched published means is expressly a reference reconstruction.
"""
from decimal import Decimal
from ..food_reference import food_bundle, FIELDS
from ..numerics import checked_product
from .common import add_parameter, feed_dry_mass, reference_gate, product_success


def calculate(repo, request, result):
    rows, missing = food_bundle(repo)
    result.feasibility_checks['reference_bundle'] = {'status': 'UNKNOWN' if missing else 'VERIFIED',
        'source_id': 'S03', 'record_ids': [item[1] for item in FIELDS.values()],
        'method': 'ratio_of_matched_published_means_not_measured_mass_specific_yield'}
    result.feasibility_checks['moisture_feasibility'] = {'status': 'UNKNOWN',
        'equipment_specific_limits': None, 'source_ids': [],
        'reason': 'The exact reference solids basis is not an equipment moisture operating limit.'}
    result.feasibility_checks['gas_chemical_energy'] = {'status': 'INSUFFICIENT_DATA', 'value': None,
        'unit': 'MJ', 'missing_parameters': ['Gas reference temperature/pressure and wet/dry gas basis',
        'Verified matching methane/biogas heating value at those gas reference conditions'],
        'reason': 'No generic methane energy constant or utilization efficiency is substituted.'}
    result.uncertainty['available_parameter_ids'] = ['P0006']
    result.missing_parameters.extend(missing)
    if missing:
        return result
    moisture = Decimal('100') - Decimal(rows['sample']['total_solids_pct'])
    result.feasibility_checks['reference_run_moisture'] = {'value': float(moisture),
        'unit': '% wet mass', 'kind': 'derived_exact_reference_sample_not_equipment_limit',
        'source_id': 'S03', 'record_id': 'W0059', 'parameter_id': 'P0006',
        'evidence_location': '100 - W0059.total_solids_pct; Table 3.5, PDF page 34'}
    if request.parameter_id != 'P0006':
        result.missing_parameters.append('Explicit applicable parameter_id P0006 / mesophilic 15-day reference selection')
        return result
    result.scenario_id = 'P0006'
    values = {}
    for name, (table, _, fields) in FIELDS.items():
        for field in fields:
            values[name, field] = add_parameter(repo, result, table, rows[name], field,
                rows[name].get('unit', '% wet feed' if field == 'total_solids_pct' else
                '% of TS' if field == 'volatile_solids_pct_ts' else
                'L reactor volume' if field == 'capacity' else 'degC target'))
    if any(value is None for value in values.values()):
        return result
    ts = values['sample', 'total_solids_pct']
    vs = values['sample', 'volatile_solids_pct_ts']
    ch4 = values['methane_fraction', 'value_typical']
    if not (0 < ts <= 100 and 0 < vs <= 100 and 0 < ch4 <= 100 and
            all(values[k, field] > 0 for k, field in [('gas_rate', 'value_typical'),
            ('vs_loading', 'value_typical'), ('reactor', 'capacity')])):
        result.missing_parameters.append('Physically valid positive loading, gas rate, reactor volume and solids fractions')
        return result
    ready = reference_gate(request, result)
    if request.moisture_pct is None and request.property_id != 'W0059':
        result.missing_parameters.append('Measured wet-basis moisture or explicitly selected exact reference sample W0059; no default')
        return result
    if request.moisture_pct is not None and Decimal(str(request.moisture_pct)) != moisture:
        result.missing_parameters.append('Moisture matching W0059 reference solids or a verified composition/process response model')
        return result
    if not ready:
        return result
    dry = feed_dry_mass(repo, request, result)
    if dry is None:
        return result
    vs_mass = checked_product(dry, vs / 100, operation='Reference VS feed mass')
    # Exact unit definitions: 1 ft = 0.3048 m, 1 lb = 0.45359237 kg.
    daily_vs = checked_product(values['vs_loading', 'value_typical'],
        values['reactor', 'capacity'] / 1000 / (0.3048 ** 3), 0.45359237,
        operation='Published reference VS input kg/day')
    daily_gas = checked_product(values['gas_rate', 'value_typical'], 24 / 1000,
        operation='Published reference biogas m3/day')
    gas = checked_product(vs_mass, daily_gas, 1 / daily_vs, operation='Reconstructed reference biogas volume')
    methane = checked_product(gas, ch4 / 100, operation='Matching reference methane volume')
    result.intermediate_products.extend([
        {'name': 'reference_total_solids_mass', 'value': dry, 'unit': 'kg TS'},
        {'name': 'reference_volatile_solids_mass', 'value': vs_mass, 'unit': 'kg VS', 'formula': 'TS_mass_kg*VS_pct_of_TS/100'},
        {'name': 'reference_VS_loading_per_day', 'value': daily_vs, 'unit': 'kg VS/day'},
        {'name': 'reference_biogas_per_day', 'value': daily_gas, 'unit': 'm3 biogas/day (source T/P unspecified)'},
        {'name': 'reference_methane_fraction', 'value': ch4, 'unit': '% vol CH4 in biogas'},
        {'name': 'raw_methane_in_digester_gas', 'value': methane, 'unit': 'm3 CH4 (source T/P unspecified)',
         'formula': 'reconstructed_biogas_volume*same_condition_CH4_volume_fraction', 'classification': 'intermediate_product_quantity'},
    ])
    result.assumptions.extend(['Input denotes the exact W0059 preprocessed reference pulp, not wet delivered market waste.',
        'VS/TS is the verified reference-sample mean, not a measurement of arbitrary user waste.',
        'The reported 30 L reactor volume is used as the volume denominator for the matched VS loading rate.',
        'A ratio of matched period means reconstructs reference throughput accounting; it is not a directly measured batch yield or a batch digestion time.'])
    result.warnings.extend(['Biogas volume and raw methane volume are different quantities; neither is upgraded biomethane.',
        'Gas reference T/P and wet/dry gas corrections are unspecified; volumes are not Nm3. Chemical energy in MJ, electricity and useful heat remain unavailable.'])
    result.limitations.append('Rounded averages were sampled at different frequencies. Their ratio is not an average of measured specific yields, a BMP test, statistical confidence interval or validated plant performance.')
    result.uncertainty['statistical'] = 'No uncertainty interval for the ratio of published means is established; covariance and paired observations are unavailable.'
    if request.desired_output != 'biogas':
        result.missing_parameters.append('Verified upgrading methane recovery and product purity; raw methane is not biomethane')
        return result
    return product_success(result, gas, 'm3 biogas (source T/P unspecified)',
        'wet_mass_kg*(1-moisture_pct/100)*(VS_pct_of_TS/100)*(biogas_L_per_h*24/1000)/(VS_loading_lb_per_ft3_day*(reactor_L/1000)/(0.3048^3)*0.45359237)')
