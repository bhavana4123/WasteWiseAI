def calculate(repo, request, result):
    result.missing_parameters.extend(['Feedstock-specific ester yield with stated mass/molar denominator', 'Triglyceride/FFA composition and pretreatment losses'])
    result.warnings.append('A strict >99% yield threshold for pure fatty acids is not a typical yield for yellow grease or used cooking oil.')
    return result
