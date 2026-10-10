"""Exact dimensional conversions; no calorific-value assumptions."""
import math
from .numerics import NumericalError, finite, checked_product

def number(value, label):
    if isinstance(value, bool):
        raise ValueError(f'{label} must be a finite number')
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        raise ValueError(f'{label} must be a finite number') from None
    if not math.isfinite(result):
        raise ValueError(f'{label} must be finite')
    return result

def mass_to_kg(value, unit):
    factors = {'g': .001, 'kg': 1, 'tonnes': 1000}
    if unit not in factors:
        raise ValueError('Mass unit must be g, kg or tonnes (metric)')
    value = number(value, 'quantity')
    if value <= 0:
        raise ValueError('quantity must be positive')
    converted = checked_product(value, factors[unit], operation='Mass conversion to kg')
    if converted <= 0:
        raise NumericalError('NUMERIC_UNDERFLOW', 'Mass conversion to kg')
    return converted

def energy_convert(value, from_unit, to_unit):
    factors = {'J': 1e-6, 'kJ': .001, 'MJ': 1, 'GJ': 1000, 'Wh': .0036, 'kWh': 3.6, 'MWh': 3600}
    if from_unit not in factors or to_unit not in factors:
        raise ValueError('Unsupported energy unit')
    # Form the ratio first: conversion to the same/larger energy unit must not
    # overflow an unnecessary intermediate in MJ.
    value = number(value, 'energy')
    converted = finite(value * (factors[from_unit] / factors[to_unit]), 'Energy unit conversion')
    if value != 0 and converted == 0:
        raise NumericalError('NUMERIC_UNDERFLOW', 'Energy unit conversion')
    return converted

def dry_mass(mass_kg, moisture_pct):
    mass_kg = mass_to_kg(mass_kg, 'kg')
    if moisture_pct is None:
        return None
    moisture_pct = number(moisture_pct, 'moisture_pct')
    if not 0 <= moisture_pct <= 100:
        raise ValueError('Moisture must be 0–100% of wet mass')
    return checked_product(mass_kg, 1 - moisture_pct / 100, operation='Dry feed mass')

def electricity_from_fuel(fuel_mj, efficiency_pct, *, auxiliary_kwh=None, efficiency_is_net=False):
    """Dimensional accounting helper. Caller must establish fuel/scale applicability.

    Net equipment efficiency includes its declared boundary only, not a whole plant.
    Unknown auxiliaries never imply zero. Already-net efficiencies are not debited twice.
    """
    efficiency_pct = number(efficiency_pct, 'efficiency')
    fuel_mj = number(fuel_mj, 'fuel energy')
    if fuel_mj < 0 or not 0 <= efficiency_pct <= 100:
        raise ValueError('Invalid fuel energy or efficiency')
    value = energy_convert(checked_product(fuel_mj, efficiency_pct / 100, operation='Fuel energy to electricity'), 'MJ', 'kWh')
    if efficiency_is_net:
        if auxiliary_kwh is not None:
            raise ValueError('Do not subtract auxiliaries from an already-net efficiency')
        return {'value': value, 'unit': 'kWh', 'classification': 'equipment_net_electricity'}
    if auxiliary_kwh is None:
        return {'value': value, 'unit': 'kWh', 'classification': 'gross_electricity'}
    auxiliary_kwh = number(auxiliary_kwh, 'auxiliary energy')
    if auxiliary_kwh < 0:
        raise ValueError('Auxiliary energy cannot be negative')
    # Negative net electricity can legitimately mean net consumption. It must
    # remain finite and retain that net boundary rather than being clipped to zero.
    return {'value': finite(value - auxiliary_kwh, 'Net electricity'), 'unit': 'kWh', 'classification': 'net_electricity'}
