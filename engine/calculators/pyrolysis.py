from .common import selected_parameter, add_parameter, feed_dry_mass, reference_gate, product_success
from ..numerics import checked_product

def calculate(repo, request, result):
    if request.desired_output not in ('bio-oil', 'biochar'):
        result.missing_parameters.extend(['Product heating values / qualified utilization equipment', 'Energy and auxiliary consumption boundary'])
        return result
    name = 'Liquid product yield' if request.desired_output == 'bio-oil' else 'Char product yield'
    row = selected_parameter(repo, request, result, 'Pyrolysis', {name})
    mass = feed_dry_mass(repo, request, result)
    ready = reference_gate(request, result)
    if row is None:
        return result
    if row['waste_subtype'] != 'Dry wood reference' or row['unit'] != '% dry feed mass':
        result.missing_parameters.append('Verified matching feedstock product mass yield')
        return result
    yield_value = add_parameter(repo, result, 'conversion_parameters', row, 'value_typical', row['unit'])
    if mass is None or yield_value is None or not ready:
        return result
    value = checked_product(mass, yield_value / 100, operation='Pyrolysis product mass')
    formula = 'wet_mass_kg*(1-moisture_pct/100)*product_mass_yield_pct/100'
    if request.desired_output == 'biochar':
        result.intermediate_products.append({'name': 'unqualified_pyrolysis_char', 'value': value, 'unit': 'kg', 'formula': formula})
        result.missing_parameters.append('Biochar contaminant, stability and end-use qualification; published char is not certified biochar')
        result.formula = formula
        return result
    result.warnings.append('Calculated liquid includes water; not pure organic oil, upgraded transport fuel or an energy value.')
    return product_success(result, value, 'kg liquid pyrolysis product including water', formula)
