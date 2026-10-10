"""Regression checks for the three independent audit findings; CSVs are read-only."""
import json
import math
import sys
from dataclasses import replace
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import CalculationInput, DataRepository, recommend
from engine.numerics import NumericalError, checked_product
from engine.recommender import calculate, CALCULATORS
from engine.units import mass_to_kg, energy_convert, electricity_from_fuel, dry_mass

@pytest.fixture
def repo():
    return DataRepository()

@pytest.fixture
def gas():
    return CalculationInput('Wood and forestry waste', 'Wood chips, Walawender 1985 run 98', 100, moisture_pct=16.52, desired_output='syngas', parameter_id='P0056', reference_mode=True)

@pytest.mark.parametrize('unit', ['g', 'kg', 'tonnes'])
@pytest.mark.parametrize('value', [0, -1, float('nan'), float('inf'), -float('inf'), True, 10**400])
def test_all_mass_units_reject_invalid_values(value, unit):
    with pytest.raises(ValueError):
        mass_to_kg(value, unit)

def test_finite_mass_that_overflows_in_tonnes_is_rejected_at_input():
    with pytest.raises(ValueError):
        CalculationInput('Wood and forestry waste', 'Dry wood reference', 1e308, 'tonnes')

def test_no_arbitrary_scientific_mass_cap_or_false_conversion_overflow():
    assert math.isfinite(mass_to_kg(1e308, 'g'))
    assert mass_to_kg(1e308, 'kg') == 1e308
    # Representability does not establish equipment capacity or design suitability.

def test_positive_mass_conversion_underflow_is_not_an_invented_zero():
    with pytest.raises(NumericalError, match='UNDERFLOW'):
        mass_to_kg(5e-324, 'g')

@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf')])
def test_energy_units_reject_non_finite_values(value):
    with pytest.raises(ValueError):
        energy_convert(value, 'MJ', 'kWh')

def test_energy_unit_overflow_and_underflow():
    with pytest.raises(NumericalError):
        energy_convert(1e308, 'MWh', 'kWh')
    with pytest.raises(NumericalError):
        energy_convert(5e-324, 'J', 'MJ')

@pytest.mark.parametrize('unit', ['MJ', 'kWh', 'MWh'])
def test_energy_identity_conversion_avoids_unnecessary_mj_intermediate(unit):
    assert energy_convert(1e308, unit, unit) == 1e308

def test_representable_large_electricity_is_not_rejected_by_intermediate_overflow():
    result = electricity_from_fuel(1e308, 50)
    assert result['classification'] == 'gross_electricity'
    assert math.isfinite(result['value'])
    assert result['value'] == pytest.approx(5e307 / 3.6)

def test_valid_zero_dry_mass_is_retained_for_100_percent_water():
    assert dry_mass(100, 100) == 0
    assert checked_product(0, 75, operation='zero reference dry feed') == 0

def test_large_pyrolysis_mass_fraction_avoids_false_percent_overflow(repo):
    request = CalculationInput('Wood and forestry waste', 'Dry wood reference', 1e307, moisture_pct=0, desired_output='bio-oil', parameter_id='P0022', reference_mode=True)
    result = calculate(request, 'Pyrolysis', repo)
    assert result.calculation_status == 'CALCULATED_REFERENCE'
    assert result.calculated_value == pytest.approx(7.5e306)
    assert math.isfinite(result.calculated_value)

def test_solid_fuel_energy_overflow_returns_structured_error_and_no_recommendation(repo):
    request = CalculationInput('Municipal solid waste', 'Dry shredded garbage sample A', 1e307, moisture_pct=0, desired_output='solid fuel energy', reference_mode=True)
    response = recommend(request, repo)
    result = response['alternatives'][0]
    assert result['calculation_status'] == 'INSUFFICIENT_DATA'
    assert result['calculated_value'] is None
    assert result['errors'][0]['code'] == 'NON_FINITE_RESULT'
    assert result['unit'] is None and not result['intermediate_products']
    assert response['recommendations'] == []
    json.dumps(response, allow_nan=False)

@pytest.mark.parametrize('quantity,operation', [(1e308, 'Dry producer-gas volume'), (3e307, 'Producer-gas chemical energy')])
def test_gas_product_and_energy_overflows_are_both_blocked(repo, gas, quantity, operation):
    result = calculate(replace(gas, quantity=quantity), 'Gasification', repo)
    assert result.calculation_status == 'INSUFFICIENT_DATA'
    assert result.calculated_value is None and not result.intermediate_products
    assert result.errors[0]['operation'] == operation
    json.dumps(result.to_dict(), allow_nan=False)

def test_methane_denominator_underflow_is_not_reported_as_zero(repo):
    request = CalculationInput('Food and organic waste', 'EBMUD source-separated delivered food waste', 5e-324, desired_output='biomethane', parameter_id='P0004', reference_mode=True)
    result = calculate(request, 'Anaerobic digestion', repo)
    assert result.calculation_status == 'INSUFFICIENT_DATA'
    assert not result.intermediate_products
    assert result.errors[0]['code'] == 'NUMERIC_UNDERFLOW'

@pytest.mark.parametrize('field', ['primary', 'intermediate', 'range', 'parameter'])
@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf')])
def test_router_guards_all_future_calculator_numeric_fields(repo, monkeypatch, field, value):
    def invalid_module(repository, request, result):
        result.calculation_status = 'CALCULATED_REFERENCE'
        result.calculated_value = 1
        if field == 'primary':
            result.calculated_value = value
        elif field == 'intermediate':
            result.intermediate_products.append({'name': 'invalid', 'value': value})
        elif field == 'range':
            result.uncertainty['range'] = {'minimum': value}
        else:
            result.parameters.append({'name': 'invalid', 'value': value})
        return result
    monkeypatch.setitem(CALCULATORS, 'Pyrolysis', invalid_module)
    request = CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, moisture_pct=0, desired_output='bio-oil', reference_mode=True)
    response = recommend(request, repo)
    assert not response['recommendations']
    assert response['alternatives'][0]['errors']
    assert response['alternatives'][0]['calculated_value'] is None
    json.dumps(response, allow_nan=False)

@pytest.mark.parametrize('intermediate', [False, True])
def test_negative_product_outputs_are_blocked(repo, monkeypatch, intermediate):
    def invalid_module(repository, request, result):
        result.calculation_status = 'CALCULATED_REFERENCE'
        result.calculated_value = 1 if intermediate else -1
        if intermediate:
            result.intermediate_products.append({'name': 'negative mass', 'value': -1})
        return result
    monkeypatch.setitem(CALCULATORS, 'Pyrolysis', invalid_module)
    request = CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, moisture_pct=0, desired_output='bio-oil', reference_mode=True)
    result = calculate(request, 'Pyrolysis', repo)
    assert result.calculation_status == 'INSUFFICIENT_DATA'
    assert result.errors[0]['code'] == 'NEGATIVE_QUANTITY'

@pytest.mark.parametrize('value', ['NaN', 'invalid', True, None])
def test_invalid_primary_type_or_missing_calculated_value_is_blocked(repo, monkeypatch, value):
    def invalid_module(repository, request, result):
        result.calculation_status = 'CALCULATED_REFERENCE'
        result.calculated_value = value
        return result
    monkeypatch.setitem(CALCULATORS, 'Pyrolysis', invalid_module)
    request = CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, moisture_pct=0, desired_output='bio-oil', reference_mode=True)
    result = calculate(request, 'Pyrolysis', repo)
    assert result.calculation_status == 'INSUFFICIENT_DATA'
    assert result.calculated_value is None and result.errors

@pytest.mark.parametrize('moisture', [16.56, 16.520001, 16.519999, 5, 100])
def test_no_undocumented_moisture_acceptance_band(repo, gas, moisture):
    result = calculate(replace(gas, moisture_pct=moisture), 'Gasification', repo)
    assert result.calculated_value is None
    assert result.feasibility_checks['moisture_feasibility']['status'] == 'UNKNOWN'
    assert result.feasibility_checks['moisture_feasibility']['equipment_specific_limits'] is None

def test_matching_source_point_is_not_an_equipment_moisture_limit(repo, gas):
    result = calculate(gas, 'Gasification', repo)
    assert result.calculation_status == 'CALCULATED_REFERENCE'
    check = result.feasibility_checks['reference_run_moisture']
    assert check['kind'] == 'published_point_observation_not_equipment_limit'
    assert check['source_id'] == 'S02' and check['record_id'] == 'P0056'
    assert 'PDF page 76' in check['evidence_location']
    assert result.feasibility_checks['moisture_feasibility']['status'] == 'UNKNOWN'

def test_missing_reference_moisture_does_not_create_a_default(repo, gas):
    row = next(r for r in repo.tables['conversion_parameters'] if r['parameter_id'] == 'P0056')
    row['operating_conditions'] = 'No moisture observation documented'
    result = calculate(gas, 'Gasification', repo)
    assert result.calculated_value is None
    assert result.feasibility_checks['moisture_feasibility']['status'] == 'UNKNOWN'
    assert 'reference_run_moisture' not in result.feasibility_checks

def test_decimal_input_literals_are_normalized_for_strict_json(repo, gas):
    request = replace(gas, quantity='100', moisture_pct='16.52')
    json.dumps(recommend(request, repo), allow_nan=False)

def test_regressions_do_not_modify_scientific_csvs(repo):
    assert repo.unchanged()
