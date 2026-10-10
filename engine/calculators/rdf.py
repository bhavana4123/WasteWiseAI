def calculate(repo, request, result):
    result.missing_parameters.extend(['Verified sorting/drying RDF or SRF product mass yield', 'Product-specific heating value and moisture basis', 'Hazard/contaminant exclusion and applicable fuel specification'])
    result.warnings.append('Raw MSW heating value is not substituted for manufactured RDF/SRF product energy.')
    return result
