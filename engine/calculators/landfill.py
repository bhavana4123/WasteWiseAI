def calculate(repo, request, result):
    result.missing_parameters.extend(['Landfill waste age/composition inventory and gas generation time basis', 'Verified site gas yield, methane fraction and collection efficiency', 'Gas utilization equipment and auxiliary consumption'])
    result.warnings.append('A newly supplied waste mass is not an existing landfill gas inventory; anaerobic-digester yields are not transferred.')
    return result
