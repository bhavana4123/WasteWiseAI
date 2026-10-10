def calculate(repo, request, result):
    result.missing_parameters.extend(['Physically consistent same-feed dry ash-free mass characterization', 'Validated matching reactor/feed conditions and scale'])
    result.warnings.append('The Detroit feed characterization is flagged for elemental closure. Its ash is not used to manufacture a coherent feed. Published biocrude is not conventional pyrolysis oil or finished biodiesel.')
    return result
