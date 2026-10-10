from .common import selected_parameter, add_parameter, feed_dry_mass, reference_gate
from ..numerics import checked_product
from ..food_reference import FOOD_SUBTYPE
from . import food_biogas

def calculate(repo, request, result):
    if request.waste_subtype == FOOD_SUBTYPE:
        return food_biogas.calculate(repo, request, result)
    result.missing_parameters.append('Mass-specific total biogas yield for the selected study' if request.desired_output == 'biogas' else 'Verified upgrading methane recovery and product purity' if request.desired_output == 'biomethane' else 'Compatible fuel-energy basis, utilization efficiency and equipment scale')
    # Methane volume is retained only as an intermediate, never relabeled biogas.
    rows = repo.conversion_parameters('Anaerobic digestion', request.waste_subtype)
    names = {r['parameter_name'] for r in rows if 'methane' in r['parameter_name'].lower() and 'yield' in r['parameter_name'].lower()}
    row = selected_parameter(repo, request, result, 'Anaerobic digestion', names)
    ready = reference_gate(request, result)
    if row is None or not ready:
        return result
    unit = row['unit']
    if unit == 'm3 CH4/t' and row['measurement_basis'] == 'dry metric tonne TS applied':
        mass = feed_dry_mass(repo, request, result)
    elif unit == 'm3 CH4/t' and row['measurement_basis'] == 'wet metric tonne delivered before processing':
        mass = request.mass_kg
    else:
        result.missing_parameters.append('Recognized methane yield denominator (not a reactor L/h rate)')
        return result
    value = add_parameter(repo, result, 'conversion_parameters', row, 'value_typical', unit)
    if value is not None and mass is not None:
        tonnes = checked_product(mass, .001, operation='Matching-basis feed mass in metric tonnes')
        result.intermediate_products.append({'name': 'raw_methane_in_digester_gas', 'value': checked_product(tonnes, value, operation='Raw methane volume'), 'unit': 'm3 CH4 (source T/P unspecified)', 'formula': 'matching_basis_feed_mass_kg/1000*methane_yield_m3_per_metric_tonne', 'classification': 'intermediate_product_quantity'})
        bounds = {}
        for field in ('value_min', 'value_max'):
            bound = add_parameter(repo, result, 'conversion_parameters', row, field, unit) if row[field] else None
            if bound is not None:
                bounds[field] = checked_product(tonnes, bound, operation='Methane descriptive range')
        result.uncertainty['published_methane_volume_range_m3'] = bounds
        result.warnings.append('Methane is not total biogas or upgraded biomethane. Gas reference temperature/pressure is unspecified; no standard methane energy constant applied.')
    return result
