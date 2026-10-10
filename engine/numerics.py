"""Numeric representation guards, independent of scientific equipment limits.

No arbitrary maximum waste mass or scientific yield is introduced. Inputs and
derived quantities must fit the finite floating-point representation in use.
"""
import math

class NumericalError(ValueError):
    def __init__(self, code, operation):
        self.code = code
        self.operation = operation
        super().__init__(f'{operation}: {code}; a finite representable number is required')

def finite(value, operation):
    if isinstance(value, bool):
        raise NumericalError('INVALID_NUMERIC_TYPE', operation)
    try:
        valid = math.isfinite(value)
    except (TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        raise NumericalError('NON_FINITE_RESULT', operation)
    return value

def checked_product(*values, operation):
    result = 1.0
    for value in values:
        finite(value, operation)
        if value < 0:
            raise NumericalError('NEGATIVE_QUANTITY', operation)
        previous = result
        result = finite(result * value, operation)
        if result == 0 and previous > 0 and value > 0:
            raise NumericalError('NUMERIC_UNDERFLOW', operation)
    return result

def validate_numeric_tree(value, path='result'):
    """Ensure even auxiliary quantities/ranges cannot leak NaN or infinity."""
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        finite(value, path)
    elif isinstance(value, dict):
        for key, item in value.items():
            validate_numeric_tree(item, f'{path}.{key}')
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            validate_numeric_tree(item, f'{path}[{index}]')
