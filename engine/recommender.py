"""Ordinal evidence/completeness ranking; alternatives never share a summed mass."""
from .models import CalculationInput
from .data_loader import DataRepository
from .calculators import anaerobic_digestion, combustion, chp, gasification, pyrolysis, fermentation, biodiesel, hydrothermal, rdf, landfill, waste_heat
from .calculators.common import base, finalize_result, numeric_failure
from .numerics import NumericalError, validate_numeric_tree
from scripts.common import CATEGORIES, TECHNOLOGIES

CALCULATORS = {
    'Anaerobic digestion': anaerobic_digestion.calculate,
    'Combustion': combustion.calculate,
    'Combined heat and power': chp.calculate,
    'Gasification': gasification.calculate,
    'Pyrolysis': pyrolysis.calculate,
    'Fermentation': fermentation.calculate,
    'Biodiesel production': biodiesel.calculate,
    'Hydrothermal conversion': hydrothermal.calculate,
    'RDF/SRF production': rdf.calculate,
    'Landfill gas recovery': landfill.calculate,
    'Industrial waste heat recovery': waste_heat.calculate,
}
OUTPUT_ROUTES = {
    'Anaerobic digestion': {'biogas', 'biomethane'},
    'Combustion': {'electricity', 'useful heat', 'solid fuel energy'},
    'Combined heat and power': {'electricity', 'useful heat'},
    'Gasification': {'syngas', 'electricity', 'useful heat'},
    'Pyrolysis': {'bio-oil', 'biochar', 'electricity', 'useful heat'},
    'Fermentation': {'ethanol'}, 'Biodiesel production': {'biodiesel'},
    'Hydrothermal conversion': {'bio-oil'}, 'RDF/SRF production': {'solid fuel energy'},
    'Landfill gas recovery': {'biogas', 'biomethane', 'electricity', 'useful heat'},
    'Industrial waste heat recovery': {'electricity', 'useful heat'},
}

def calculate(request, technology, repository=None):
    repo = repository or DataRepository()
    if request.waste_category.casefold() not in {x.casefold() for x in CATEGORIES}:
        raise ValueError('Unknown waste category')
    if request.property_id and not repo.waste_properties(request.waste_category, request.waste_subtype, request.property_id):
        raise ValueError('property_id does not belong to the requested published waste sample')
    if technology not in CALCULATORS:
        raise ValueError('Unknown technology')
    mappings = [m for m in repo.applicable_technologies(request.waste_category, request.waste_subtype) if m['technology'] == technology]
    if len(mappings) > 1:
        raise ValueError('Ambiguous mapping: select a more specific published subtype')
    result = base(request, technology, mappings[0] if mappings else None)
    if result.calculation_status in ('NOT_APPLICABLE', 'RESTRICTED'):
        return result
    if request.desired_output not in OUTPUT_ROUTES[technology]:
        result.calculation_status = 'NOT_APPLICABLE'
        result.missing_parameters.append('Technology route capable of the requested output')
        return result
    try:
        return finalize_result(CALCULATORS[technology](repo, request, result))
    except NumericalError as error:
        return numeric_failure(result, error)
    except (OverflowError, FloatingPointError):
        return numeric_failure(result, NumericalError('NUMERIC_OVERFLOW', 'Technology calculation'))

def recommend(request: CalculationInput, repository=None):
    repo = repository or DataRepository()
    if request.waste_category.casefold() not in {x.casefold() for x in CATEGORIES}:
        raise ValueError('Unknown waste category')
    if request.technology_preference and request.technology_preference not in TECHNOLOGIES:
        raise ValueError('Unknown technology preference')
    maps = repo.applicable_technologies(request.waste_category, request.waste_subtype)
    technologies = sorted({m['technology'] for m in maps if request.desired_output in OUTPUT_ROUTES[m['technology']]})
    if request.technology_preference:
        technologies = [request.technology_preference]
    results = [calculate(request, tech, repo).to_dict() for tech in technologies]
    supported = [r for r in results if r['calculation_status'] == 'CALCULATED_REFERENCE']
    # Ties retain alphabetical ordering; incomparable fuels/products are never ranked by magnitude.
    ranking = [{'rank': 1, 'technology': r['technology'], 'scenario_id': r['scenario_id'], 'reason': 'Verified matching reference parameters; requested quantity calculable; conditional feed/scale validation still required', 'scope': 'reference assessment, not installation recommendation'} for r in supported]
    response = {
        'input': {**request.__dict__, 'mass_kg': request.mass_kg},
        'status': 'REFERENCE_RESULTS_AVAILABLE' if supported else 'INSUFFICIENT_DATA' if results else 'NO_APPLICABLE_VERIFIED_MAPPING',
        'recommendations': ranking, 'alternatives': results,
        'allocation': {'mode': 'mutually_exclusive_alternatives', 'mass_per_alternative_kg': request.mass_kg, 'combined_output': None, 'note': 'Each alternative uses the same input once; outputs across alternatives must not be added. No allocation/combined-system solver is implemented.'},
        'dataset_issues': repo.issues,
        'warnings': ['Reference-mode results are not equipment performance predictions.'] if request.reference_mode else [],
    }
    validate_numeric_tree(response)
    return response
