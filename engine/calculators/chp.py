def calculate(repo, request, result):
    equipment = repo.equipment_performance('Combined heat and power')
    result.missing_parameters.extend(['Verified waste-derived fuel energy / gas normalization', 'Manufacturer-qualified waste-gas efficiency (existing efficiencies are natural-gas-only)', 'Operating duration and equipment load/scale applicability', 'Complete auxiliary-energy boundary for net plant electricity'])
    result.uncertainty['equipment_records_not_applied'] = [r['record_id'] for r in equipment]
    result.warnings.append('Natural-gas baseload efficiencies are not transferred to biogas or solid waste. Microturbine net efficiencies already include their specified fuel-gas booster; do not subtract it twice.')
    return result
