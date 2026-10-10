from .common import add_parameter, feed_dry_mass, reference_gate, product_success
from ..numerics import checked_product

def calculate(repo, request, result):
    if request.desired_output != 'solid fuel energy':
        result.missing_parameters.extend(['Verified matching-basis feedstock heating value', 'Solid-fuel-specific electrical/thermal efficiency and capacity/duration', 'Auxiliary energy consumption for net output'])
        return result
    rows = repo.waste_properties(request.waste_category, request.waste_subtype, request.property_id)
    if len(rows) != 1:
        result.missing_parameters.append('Explicit coherent property_id with known heating-value basis')
        return result
    row = rows[0]
    if row.get('model_ready') == 'false':
        result.missing_parameters.append('Physically consistent property record (published quality flag blocks calculation)')
        return result
    basis = row['heating_value_basis'].lower()
    if 'dry' not in basis or 'ash-free' in basis or 'not explicitly' in basis:
        result.missing_parameters.append('Unambiguous heating-value mass basis (dry ash-free requires same-sample ash)')
        return result
    mass = feed_dry_mass(repo, request, result)
    field = 'hhv_mj_kg' if row['hhv_mj_kg'] else 'lhv_mj_kg'
    h = add_parameter(repo, result, 'waste_properties', row, field, 'MJ/kg dry feed')
    ready = reference_gate(request, result)
    if mass is None or h is None or not ready:
        return result
    result.warnings.append('Chemical feed energy only; no combustion recovery, electricity, RDF processing yield or evaporation duty has been credited.')
    result.assumptions.append('The exact published sample is used; non-hazardous/non-recyclable feed suitability still requires confirmation.')
    return product_success(result, checked_product(mass, h, operation='Theoretical solid-fuel chemical energy'), f'MJ {"HHV" if field == "hhv_mj_kg" else "LHV"}', 'wet_mass_kg*(1-moisture_pct/100)*dry_feed_heating_value_MJ_per_kg', 'theoretical_chemical_energy')
