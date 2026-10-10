"""Independent published-value fixtures, not expectations computed by engine code.

Transcribed during this audit from fresh original PDFs:
S07 PDF/printed page 5, Table 1; S02 PDF page 76 / printed p68, Table 7-8;
S01 PDF p182 / printed p201, Refuse; S03 PDF p48 / printed p33, Table 3.11.
Expected values use literal published constants and Decimal mass accounting here.
Production imports are used ONLY to obtain observed outputs.
ROUNDING_ABS is floating-point representation tolerance, not predictive uncertainty.
No xfail or skips conceal scientific failures.
"""
import math
import re
import sys
from decimal import Decimal
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import CalculationInput, DataRepository, recommend
from engine.recommender import calculate

ROUNDING_ABS = 1e-8

# run, moisture %wet, gas HHV MJ/m3, gas m3/kg dry chips, dry kg/h,
# source printed energy yield MJ/kg dry chips, material-balance closure %.
# Independently transcribed from the rendered original; never read from CSV.
GAS_RUNS = [
    ('98', '16.52', '5.33', '2.22', '26.7', '11.82', '98.9'),
    ('910', '16.52', '5.18', '2.28', '26.7', '11.82', '98.3'),
    ('920', '6.01', '5.33', '2.48', '33.6', '13.14', '96.6'),
    ('927', '8.11', '5.63', '2.54', '41.2', '14.31', '85.4'),
    ('922', '5.75', '5.44', '1.43', '47.8', '7.76', '85.1'),
    ('101', '6.99', '5.59', '2.18', '48.7', '12.19', '98.6'),
    ('929', '7.41', '5.63', '2.10', '48.8', '11.82', '99.5'),
    ('1011', '7.31', '5.44', '2.55', '49.5', '13.84', '91.6'),
    ('1015', '7.95', '5.33', '2.73', '52.3', '14.52', '88.8'),
    ('924', '5.50', '5.66', '1.62', '53.7', '9.11', '91.8'),
    ('106', '6.67', '5.48', '1.95', '54.3', '10.68', '95.4'),
    ('123', '14.61', '5.51', '1.90', '54.3', '10.44', '94.2'),
    ('104', '7.72', '5.55', '2.61', '63.7', '14.50', '92.6'),
    ('1129', '14.27', '5.59', '2.85', '68.9', '15.89', '91.9'),
    ('121', '15.07', '5.63', '1.39', '72.5', '7.81', '80.4'),
    ('1119', '16.32', '5.74', '2.11', '74.6', '12.08', '97.3'),
    ('1117', '11.26', '5.78', '2.30', '85.4', '13.31', '97.0'),
    ('1110', '11.56', '5.74', '1.79', '119.7', '10.23', '91.0'),
    ('1221', '10.67', '5.44', '2.10', '125.5', '11.42', '98.2'),
]

@pytest.fixture(scope='module')
def repo():
    return DataRepository()

def assert_rounding(actual, expected):
    assert actual == pytest.approx(float(expected), rel=0, abs=ROUNDING_ABS)

@pytest.mark.parametrize('parameter_id,expected,condition', [
    ('P0022', '67.5', 'fast; around 500 degC; hot vapour residence approximately 1 s'),
    ('P0025', '45', 'intermediate; around 500 degC; hot vapour residence approximately 10-20 s'),
    ('P0028', '27', 'slow carbonisation; around 400 degC; very long solids residence time'),
])
def test_golden_pyrolysis_liquid(repo, parameter_id, expected, condition):
    request = CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, moisture_pct=10, desired_output='bio-oil', parameter_id=parameter_id, reference_mode=True)
    result = calculate(request, 'Pyrolysis', repo)
    assert result.calculation_status == 'CALCULATED_REFERENCE'
    assert_rounding(result.calculated_value, expected)
    assert 'including water' in result.unit
    assert result.gross_vs_net_classification == 'intermediate_product_quantity'
    assert result.source_ids == ['S07']
    assert next(p['operating_conditions'] for p in result.parameters if p.get('record_id') == parameter_id) == condition

@pytest.mark.parametrize('index,run_data', list(enumerate(GAS_RUNS)), ids=[r[0] for r in GAS_RUNS])
def test_golden_gas_volume_and_energy(repo, index, run_data):
    run, moisture, hhv, gas_yield, flow, energy_yield, closure = run_data
    dry_kg = Decimal('1000') * (Decimal('100') - Decimal(moisture)) / Decimal('100')
    expected_volume = dry_kg * Decimal(gas_yield)
    expected_energy = expected_volume * Decimal(hhv)
    request = CalculationInput('Wood and forestry waste', f'Wood chips, Walawender 1985 run {run}', 1, 'tonnes', float(moisture), 'syngas', parameter_id=f'P{56+4*index:04}', reference_mode=True)
    result = calculate(request, 'Gasification', repo)
    assert_rounding(result.calculated_value, expected_volume)
    assert_rounding(result.intermediate_products[0]['value'], expected_energy)
    assert result.intermediate_products[0]['unit'] == 'MJ HHV'
    assert 'unspecified' in result.unit and 'Nm3' not in result.unit
    used = {p['field']: p for p in result.parameters if p.get('record_id') == request.parameter_id}
    conditions = used['value_typical']['operating_conditions']
    assert f'dry chip rate {flow} kg/h' in conditions
    reported_moisture = re.search(r'chip moisture ([0-9.]+)% wet basis', conditions).group(1)
    assert Decimal(reported_moisture) == Decimal(moisture)

@pytest.mark.parametrize('letter,hhv,expected', [('A', '18.5', '1480'), ('B', '19.85', '1588'), ('C', '20.04', '1603.2'), ('D', '20.05', '1604')])
def test_golden_solid_fuel_chemical_energy(repo, letter, hhv, expected):
    # 100 kg wet at 20% water -> 80 kg dry; original J/g / 1000 -> MJ/kg.
    request = CalculationInput('Municipal solid waste', 'Dry shredded garbage sample '+letter, 100, moisture_pct=20, desired_output='solid fuel energy', reference_mode=True)
    result = calculate(request, 'Combustion', repo)
    assert_rounding(result.calculated_value, expected)
    assert_rounding(next(p['value'] for p in result.parameters if p.get('field') == 'hhv_mj_kg'), hhv)
    assert result.unit == 'MJ HHV'
    assert result.gross_vs_net_classification == 'theoretical_chemical_energy'

@pytest.mark.parametrize('subtype,parameter_id,moisture,expected,low,high', [
    ('EBMUD food waste pulp', 'P0001', 90, '42', '30', '53'),
    ('EBMUD food waste pulp', 'P0002', 90, '30', '20', '45'),
    ('EBMUD municipal wastewater solids', 'P0003', 90, '31', '23', '39'),
    ('EBMUD source-separated delivered food waste', 'P0004', None, '100', '75', '135'),
    ('EBMUD source-separated delivered food waste', 'P0005', None, '75', '50', '110'),
])
def test_golden_methane_intermediate(repo, subtype, parameter_id, moisture, expected, low, high):
    category = 'Sewage sludge' if 'municipal wastewater' in subtype else 'Food and organic waste'
    request = CalculationInput(category, subtype, 1, 'tonnes', moisture, 'biomethane', parameter_id=parameter_id, reference_mode=True)
    result = calculate(request, 'Anaerobic digestion', repo)
    assert result.calculated_value is None and result.calculation_status == 'INSUFFICIENT_DATA'
    assert_rounding(result.intermediate_products[0]['value'], expected)
    assert result.intermediate_products[0]['name'] == 'raw_methane_in_digester_gas'
    assert_rounding(result.uncertainty['published_methane_volume_range_m3']['value_min'], low)
    assert_rounding(result.uncertainty['published_methane_volume_range_m3']['value_max'], high)
    assert 'Nm3' not in result.intermediate_products[0]['unit']

@pytest.mark.parametrize('pid,expected', [('P0023', '10.8'), ('P0026', '18'), ('P0029', '31.5')])
def test_golden_char_is_intermediate_only(repo, pid, expected):
    request = CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, moisture_pct=10, desired_output='biochar', parameter_id=pid, reference_mode=True)
    result = calculate(request, 'Pyrolysis', repo)
    assert_rounding(result.intermediate_products[0]['value'], expected)
    assert result.calculated_value is None

@pytest.mark.parametrize('quantity,unit', [(100000, 'g'), (100, 'kg'), (.1, 'tonnes')])
@pytest.mark.parametrize('pathway', ['pyrolysis', 'gasification', 'solid_fuel', 'methane'])
def test_golden_mass_units_equivalent(repo, quantity, unit, pathway):
    if pathway == 'pyrolysis':
        request = CalculationInput('Wood and forestry waste', 'Dry wood reference', quantity, unit, 10, 'bio-oil', parameter_id='P0022', reference_mode=True)
        assert_rounding(calculate(request, 'Pyrolysis', repo).calculated_value, '67.5')
    elif pathway == 'gasification':
        request = CalculationInput('Wood and forestry waste', 'Wood chips, Walawender 1985 run 98', quantity, unit, 16.52, 'syngas', parameter_id='P0056', reference_mode=True)
        assert_rounding(calculate(request, 'Gasification', repo).calculated_value, '185.3256')
    elif pathway == 'solid_fuel':
        request = CalculationInput('Municipal solid waste', 'Dry shredded garbage sample A', quantity, unit, 20, 'solid fuel energy', reference_mode=True)
        assert_rounding(calculate(request, 'Combustion', repo).calculated_value, '1480')
    else:
        request = CalculationInput('Food and organic waste', 'EBMUD food waste pulp', quantity, unit, 90, 'biogas', parameter_id='P0001', reference_mode=True)
        assert_rounding(calculate(request, 'Anaerobic digestion', repo).intermediate_products[0]['value'], '4.2')

@pytest.mark.parametrize('quantity', [0, -1, float('nan'), float('inf'), -float('inf'), True, None, 'bad'])
def test_independent_invalid_quantities(quantity):
    with pytest.raises(ValueError):
        CalculationInput('Wood and forestry waste', 'Dry wood reference', quantity)

@pytest.mark.parametrize('moisture,expected', [(0, '75'), (100, '0')])
def test_independent_moisture_arithmetic_boundaries(repo, moisture, expected):
    request = CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, moisture_pct=moisture, desired_output='bio-oil', parameter_id='P0022', reference_mode=True)
    assert_rounding(calculate(request, 'Pyrolysis', repo).calculated_value, expected)

def test_independent_missing_moisture(repo):
    request = CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, desired_output='bio-oil', parameter_id='P0022', reference_mode=True)
    result = calculate(request, 'Pyrolysis', repo)
    assert result.calculated_value is None and result.missing_parameters

@pytest.mark.parametrize('output', ['electricity', 'useful heat'])
@pytest.mark.parametrize('category,subtype,technology', [
    ('Wood and forestry waste', 'Dry wood reference', 'Pyrolysis'),
    ('Wood and forestry waste', 'Wood chips, Walawender 1985 run 98', 'Gasification'),
    ('Municipal solid waste', 'Dry shredded garbage sample A', 'Combustion'),
    ('Food and organic waste', 'Source-separated food waste', 'Combined heat and power'),
    ('Industrial waste heat', 'Industrial hot gases and liquids', 'Industrial waste heat recovery'),
    ('Landfill waste', 'Biodegradable waste already in MSW landfill', 'Landfill gas recovery'),
])
def test_independent_energy_forecasts_remain_blocked(repo, output, category, subtype, technology):
    request = CalculationInput(category, subtype, 100, moisture_pct=10, desired_output=output, reference_mode=True)
    result = calculate(request, technology, repo)
    assert result.calculated_value is None
    assert result.calculation_status == 'INSUFFICIENT_DATA'
    assert not recommend(request, repo)['recommendations']

def test_independent_incompatible_and_restricted(repo):
    request = CalculationInput('Hazardous and medical waste', 'Regulated medical waste', 100, desired_output='electricity', technology_preference='Combustion')
    assert calculate(request, 'Combustion', repo).calculation_status == 'RESTRICTED'
    assert recommend(request, repo)['recommendations'] == []
    incompatible = CalculationInput('Inert waste', 'Glass', 100, desired_output='biodiesel')
    assert calculate(incompatible, 'Biodiesel production', repo).calculation_status == 'NOT_APPLICABLE'

def test_independent_mass_conversion_overflow_must_be_rejected():
    # Finite user input can overflow after conversion; never return an infinite mass.
    with pytest.raises(ValueError):
        request = CalculationInput('Wood and forestry waste', 'Dry wood reference', 1e308, 'tonnes')
        _ = request.mass_kg

def test_independent_energy_overflow_must_be_rejected_or_blocked(repo):
    request = CalculationInput('Municipal solid waste', 'Dry shredded garbage sample A', 1e307, moisture_pct=0, desired_output='solid fuel energy', reference_mode=True)
    try:
        result = calculate(request, 'Combustion', repo)
    except ValueError:
        return
    assert result.calculated_value is None or math.isfinite(result.calculated_value), 'An infinite energy must not be labeled CALCULATED_REFERENCE'

def test_independent_moisture_tolerance_requires_published_support(repo):
    # Source moisture 16.52% is displayed to .01%. 16.56 differs by .04 percentage
    # points, exceeding +/- .005 rounding; no response model supports the .05 band.
    request = CalculationInput('Wood and forestry waste', 'Wood chips, Walawender 1985 run 98', 100, moisture_pct=16.56, desired_output='syngas', parameter_id='P0056', reference_mode=True)
    result = calculate(request, 'Gasification', repo)
    assert result.calculated_value is None, 'Unpublished moisture acceptance band is not a source-verified operating condition'
