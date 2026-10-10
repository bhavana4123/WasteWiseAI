def calculate(repo, request, result):
    result.missing_parameters.extend(['Same-sample glucan/xylan and fermentable-sugar mass fractions', 'Verified pretreatment and hydrolysis mass balance', 'Documented sugar-to-ethanol stoichiometric basis and matching integrated yield'])
    result.warnings.append('Cellulose/xylose theoretical-yield percentages are not ethanol mass per kg whole waste. Incompatible pilot runs are not averaged.')
    return result
