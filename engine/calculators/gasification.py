import re
from decimal import Decimal
from .common import selected_parameter, add_parameter, feed_dry_mass, reference_gate, product_success
from ..numerics import checked_product

def calculate(repo, request, result):
    result.feasibility_checks['moisture_feasibility'] = {
        'status': 'UNKNOWN', 'equipment_specific_limits': None,
        'source_ids': [],
        'reason': 'No verified equipment-specific moisture operating limits are available. A published run moisture is a reference observation, not a permitted operating range.',
    }
    result.warnings.append('Gasifier moisture feasibility is unknown; no default moisture threshold or equipment operating range is applied.')
    if request.desired_output != 'syngas':
        result.missing_parameters.extend(['Gas-compatible equipment efficiency and capacity/duration', 'Verified gas fuel specification and auxiliary energy consumption'])
        return result
    row = selected_parameter(repo, request, result, 'Gasification', {'Dry producer gas volume yield'})
    mass = feed_dry_mass(repo, request, result)
    ready = reference_gate(request, result)
    if row is None:
        return result
    if row['unit'] != 'm3 gas/kg dry chips' or 'Walawender 1985 run ' not in row['waste_subtype']:
        result.missing_parameters.append('Compatible dry-chip gas volume yield basis')
        return result
    moisture = re.search(r'chip moisture ([0-9.]+)% wet basis', row['operating_conditions'])
    if moisture is None:
        result.missing_parameters.append('Documented moisture observation for the selected reference run; equipment moisture feasibility remains unknown')
        return result
    result.feasibility_checks['reference_run_moisture'] = {
        'value': float(moisture.group(1)), 'unit': '% wet mass',
        'kind': 'published_point_observation_not_equipment_limit',
        'source_id': row['source_id'], 'record_id': row['parameter_id'],
        'evidence_location': row['evidence_location'],
    }
    # This is exact reference-condition identity, not a feasibility limit. No
    # tolerance is invented and no plant performance is extrapolated to other water
    # contents. Decimal handles equivalent literals such as 5.50 and 5.5 equally.
    if request.moisture_pct is not None and Decimal(str(request.moisture_pct)) != Decimal(moisture.group(1)):
        result.missing_parameters.append('Feed moisture matching the selected gasification run or verified moisture-response model')
        result.warnings.append('A dry-mass conversion does not correct moisture-dependent gasifier performance.')
        return result
    yield_value = add_parameter(repo, result, 'conversion_parameters', row, 'value_typical', row['unit'])
    if mass is None or yield_value is None or not ready:
        return result
    volume = checked_product(mass, yield_value, operation='Dry producer-gas volume')
    result.warnings.append('Output is dry producer gas at the publication’s unspecified temperature/pressure; it is not Nm3, biomethane or electricity.')
    same_run = [r for r in repo.conversion_parameters('Gasification', row['waste_subtype']) if r['parameter_name'] == 'Dry producer gas HHV' and r['source_id'] == row['source_id'] and r['operating_conditions'] == row['operating_conditions']]
    if len(same_run) == 1 and repo.verified_field('conversion_parameters', same_run[0], 'value_typical') and same_run[0]['unit'] == 'MJ/m3':
        hhv = add_parameter(repo, result, 'conversion_parameters', same_run[0], 'value_typical', 'MJ/m3 dry gas (source reference conditions)')
        result.intermediate_products.append({'name': 'recoverable_producer_gas_chemical_energy_reference', 'value': checked_product(volume, hhv, operation='Producer-gas chemical energy'), 'unit': 'MJ HHV', 'formula': 'wet_mass_kg*(1-moisture_pct/100)*same_run_gas_yield*same_run_gas_HHV', 'classification': 'recoverable_fuel_energy', 'boundary': 'Gas energy before downstream utilization; no electricity or drying-energy deduction.'})
    return product_success(result, volume, 'm3 dry producer gas (source T/P unspecified)', 'wet_mass_kg*(1-moisture_pct/100)*gas_yield_m3_per_kg_dry')
