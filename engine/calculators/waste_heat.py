def calculate(repo, request, result):
    result.missing_parameters.extend(['Stream mass flow and operating duration (batch waste quantity is insufficient)', 'Stream-specific heat capacity or enthalpy', 'Measured source/sink temperatures and recoverable temperature difference', 'Qualified heat exchanger/recovery efficiency and auxiliary energy'])
    result.warnings.append('Published source temperature ranges alone do not establish recoverable energy or electricity.')
    return result
