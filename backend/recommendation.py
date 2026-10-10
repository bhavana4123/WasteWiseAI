"""Interface recommendations from existing engine checks; no new scientific model."""
from engine import CalculationInput
from engine.recommender import calculate

# Stable display tie-break only; products are never ranked by yield/energy magnitude.
OUTPUT_ORDER = ['bio-oil', 'syngas', 'biogas', 'solid fuel energy', 'ethanol', 'biodiesel', 'biomethane', 'biochar']
BLOCKED = {'electricity', 'useful heat'}


def assess_outputs(repo, category, subtype, pathway):
    assessments = []
    if not pathway['default_eligible']:
        return assessments, None
    for output in pathway['requested_outputs']:
        # Unit-mass, unknown-moisture, non-reference check discovers requirements.
        # It is not a forecast and no calculated quantity is exposed here.
        request = CalculationInput(category, subtype, 1.0, 'kg', None, output,
                                   pathway['technology'], reference_mode=False)
        result = calculate(request, pathway['technology'], repo)
        identifiers = result.uncertainty.get('available_parameter_ids', [])
        if result.scenario_id:
            identifiers = [result.scenario_id]
        exact_rows = repo.conversion_parameters(pathway['technology'], subtype)
        identifiers = sorted({row['parameter_id'] for row in exact_rows
                              if row['parameter_id'] in identifiers
                              and repo.verified_field('conversion_parameters', row, 'value_typical')})
        verified_used = any(p.get('record_id') and p.get('origin') != 'user' for p in result.parameters)
        assessments.append(dict(output=output, forecast_blocked=output in BLOCKED,
                                has_verified_parameters=bool(identifiers) or verified_used,
                                matching_parameter_ids=identifiers,
                                study_selection_required=len(identifiers) > 1,
                                calculation_status=result.calculation_status,
                                missing_parameters=result.missing_parameters,
                                explanation=('Equipment energy forecast remains blocked.' if output in BLOCKED else
                                             'Exact verified parameters exist; study conditions, moisture and explicit reference acknowledgement may still be required.' if identifiers or verified_used else
                                             'Verified mapping only; required matching calculation parameters are absent or not established.')))
    assessments.sort(key=lambda a: (a['forecast_blocked'], not a['has_verified_parameters'],
                                   len(a['missing_parameters']),
                                   OUTPUT_ORDER.index(a['output']) if a['output'] in OUTPUT_ORDER else 99,
                                   a['output']))
    recommended = next((a['output'] for a in assessments if not a['forecast_blocked']), None)
    return assessments, recommended


def recommendation_key(pathway):
    assessment = next((a for a in pathway['output_assessments'] if a['output'] == pathway['recommended_output']), None)
    compatibility = {'demonstrated': 2, 'feasible': 2, 'conditional': 1}.get(pathway['feasibility_status'], 0)
    return (not pathway['default_eligible'], assessment is None,
            not bool(assessment and assessment['has_verified_parameters']),
            -compatibility, len(assessment['missing_parameters']) if assessment else 999,
            pathway['technology'])
