"""Dimensional, basis, provenance and conservative applicability regression tests."""
import csv
import json
import re
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import CalculationInput, DataRepository, recommend
from engine.data_loader import DataError
from engine.recommender import calculate, CALCULATORS
from engine.units import mass_to_kg, energy_convert, dry_mass, electricity_from_fuel

@pytest.fixture
def repo():
    return DataRepository()

@pytest.fixture
def wood():
    return CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, 'kg', 10, 'bio-oil', parameter_id='P0022', reference_mode=True)

@pytest.mark.parametrize('value,unit,expected', [(1000, 'g', 1), (1, 'kg', 1), (1, 'tonnes', 1000)])
def test_mass(value, unit, expected):
    assert mass_to_kg(value, unit) == expected

@pytest.mark.parametrize('value,a,b,expected', [(3.6, 'MJ', 'kWh', 1), (1, 'MWh', 'MJ', 3600), (1, 'GJ', 'kWh', 1000/3.6), (3600000, 'J', 'kWh', 1)])
def test_energy(value, a, b, expected):
    assert energy_convert(value, a, b) == pytest.approx(expected)

@pytest.mark.parametrize('quantity,unit', [(0, 'kg'), (-1, 'kg'), (float('nan'), 'kg'), (float('inf'), 'g'), (True, 'kg'), (1, 'tons'), (None, 'kg')])
def test_invalid_mass(quantity, unit):
    with pytest.raises(ValueError):
        mass_to_kg(quantity, unit)

@pytest.mark.parametrize('moisture', [-1, 101, float('nan'), float('inf'), True])
def test_invalid_moisture(wood, moisture):
    with pytest.raises(ValueError):
        replace(wood, moisture_pct=moisture)

def test_unknown_moisture_is_not_zero(repo, wood):
    result = calculate(replace(wood, moisture_pct=None), 'Pyrolysis', repo)
    assert result.calculated_value is None
    assert any('moisture' in m for m in result.missing_parameters)
    assert dry_mass(100, None) is None

def test_dry_wet_mass_consistency(repo, wood):
    assert calculate(wood, 'Pyrolysis', repo).calculated_value == pytest.approx(67.5)
    assert calculate(replace(wood, moisture_pct=0), 'Pyrolysis', repo).calculated_value == 75
    assert calculate(replace(wood, moisture_pct=100), 'Pyrolysis', repo).calculated_value == 0

def test_no_average_across_modes(repo, wood):
    result = calculate(replace(wood, parameter_id=None), 'Pyrolysis', repo)
    assert result.calculated_value is None
    assert result.uncertainty['available_parameter_ids'] == ['P0022', 'P0025', 'P0028']
    assert calculate(replace(wood, parameter_id='P0025'), 'Pyrolysis', repo).calculated_value == 45

def test_yields_not_transferred_to_sludge(repo):
    request = CalculationInput('Sewage sludge', 'Dried sewage sludge', 100, moisture_pct=0, desired_output='bio-oil', parameter_id='P0022', reference_mode=True)
    result = calculate(request, 'Pyrolysis', repo)
    assert result.calculated_value is None and result.calculation_status == 'INSUFFICIENT_DATA'

def test_gasification_same_run_basis(repo):
    request = CalculationInput('Wood and forestry waste', 'Wood chips, Walawender 1985 run 98', 100, moisture_pct=16.52, desired_output='syngas', parameter_id='P0056', reference_mode=True)
    result = calculate(request, 'Gasification', repo)
    assert result.calculated_value == pytest.approx(100*.8348*2.22)
    assert result.intermediate_products[0]['value'] == pytest.approx(result.calculated_value*5.33)
    assert 'Nm3' not in result.unit
    assert {p['record_id'] for p in result.parameters if 'record_id' in p} == {'P0055', 'P0056'}

def test_wrong_run_not_selected(repo):
    request = CalculationInput('Wood and forestry waste', 'Wood chips, Walawender 1985 run 98', 100, moisture_pct=16.52, desired_output='syngas', parameter_id='P0060', reference_mode=True)
    assert calculate(request, 'Gasification', repo).calculated_value is None

def test_gas_moisture_conflict_not_fixed_by_dry_conversion(repo):
    request = CalculationInput('Wood and forestry waste', 'Wood chips, Walawender 1985 run 98', 100, moisture_pct=5, desired_output='syngas', parameter_id='P0056', reference_mode=True)
    result = calculate(request, 'Gasification', repo)
    assert result.calculated_value is None
    assert any('moisture matching' in m for m in result.missing_parameters)

def test_property_id_cannot_select_an_unrelated_sample(repo, wood):
    with pytest.raises(ValueError):
        calculate(replace(wood, property_id='W0046'), 'Pyrolysis', repo)

def test_source_traceability(repo, wood):
    result = calculate(wood, 'Pyrolysis', repo)
    assert result.source_ids == ['S07']
    assert any(e.get('evidence_file') == 'data/processed/S07_page_005.txt' for e in result.evidence)
    assert repo.source('S07')['source_url'].startswith('https://')
    assert all(repo.source_is_verified(s) for s in result.source_ids)

def test_unverified_numeric_ledger_blocks(repo, wood):
    repo.ledger[('conversion_parameters', 'P0022', 'value_typical')][0]['verification_status'] = 'unverified'
    assert calculate(wood, 'Pyrolysis', repo).calculated_value is None

def test_missing_or_tampered_evidence_blocks(repo, wood):
    repo.ledger[('conversion_parameters', 'P0022', 'value_typical')][0]['evidence_sha256'] = 'bad'
    assert calculate(wood, 'Pyrolysis', repo).calculated_value is None

def test_source_hash_blocks(repo, wood):
    repo.sources['S07']['sha256'] = 'bad'
    assert calculate(wood, 'Pyrolysis', repo).calculation_status == 'NOT_APPLICABLE'

def test_changed_number_not_verified(repo, wood):
    repo.tables['conversion_parameters'][21]['value_typical'] = '99'
    assert calculate(wood, 'Pyrolysis', repo).calculated_value is None

def test_changed_basis_not_verified(repo, wood):
    repo.tables['conversion_parameters'][21]['measurement_basis'] = 'wet mass'
    assert calculate(wood, 'Pyrolysis', repo).calculated_value is None

def test_changed_unit_not_verified(repo, wood):
    repo.tables['conversion_parameters'][21]['unit'] = '% wet feed mass'
    assert calculate(wood, 'Pyrolysis', repo).calculated_value is None

def test_all_published_gasification_runs_remain_separate(repo):
    rows = [r for r in repo.conversion_parameters('Gasification') if r['parameter_name'] == 'Dry producer gas volume yield']
    assert len(rows) == 19
    for row in rows:
        moisture = float(re.search(r'chip moisture ([0-9.]+)% wet basis', row['operating_conditions']).group(1))
        request = CalculationInput('Wood and forestry waste', row['waste_subtype'], 100, moisture_pct=moisture, desired_output='syngas', parameter_id=row['parameter_id'], reference_mode=True)
        result = calculate(request, 'Gasification', repo)
        assert result.calculation_status == 'CALCULATED_REFERENCE'
        assert result.calculated_value == pytest.approx(100*(1-moisture/100)*float(row['value_typical']))
        assert len(result.intermediate_products) == 1

def test_all_pyrolysis_modes_and_garbage_reference_samples(repo):
    for parameter_id, yield_pct in [('P0022', 75), ('P0025', 50), ('P0028', 30)]:
        request = CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, moisture_pct=0, desired_output='bio-oil', parameter_id=parameter_id, reference_mode=True)
        assert calculate(request, 'Pyrolysis', repo).calculated_value == yield_pct
    for letter, hhv in [('A', 18.5), ('B', 19.85), ('C', 20.04), ('D', 20.05)]:
        request = CalculationInput('Municipal solid waste', 'Dry shredded garbage sample '+letter, 100, moisture_pct=0, desired_output='solid fuel energy', reference_mode=True)
        assert calculate(request, 'Combustion', repo).calculated_value == pytest.approx(100*hhv)

def test_known_manure_mapping_has_no_invented_yield(repo):
    row = next(r for r in repo.tables['waste_properties'] if r['waste_category'] == 'Animal manure')
    request = CalculationInput('Animal manure', row['waste_subtype'], 100, desired_output='biogas')
    result = calculate(request, 'Anaerobic digestion', repo)
    assert result.calculation_status == 'INSUFFICIENT_DATA'
    assert result.calculated_value is None

def test_dataset_physical_bounds_rejected(repo):
    repo.tables['waste_properties'][0]['moisture_pct'] = '101'
    with pytest.raises(DataError):
        repo.validate()

def test_missing_parameter_basis_rejected(repo):
    repo.tables['conversion_parameters'][0]['measurement_basis'] = ''
    with pytest.raises(DataError):
        repo.validate()

def test_biogas_not_methane_and_wet_yield_needs_no_moisture(repo):
    request = CalculationInput('Food and organic waste', 'EBMUD source-separated delivered food waste', 1, 'tonnes', desired_output='biomethane', parameter_id='P0004', reference_mode=True)
    result = calculate(request, 'Anaerobic digestion', repo)
    assert result.calculated_value is None
    assert result.intermediate_products[0]['value'] == 100
    assert result.uncertainty['published_methane_volume_range_m3'] == {'value_min': 75, 'value_max': 135}
    assert result.intermediate_products[0]['name'] == 'raw_methane_in_digester_gas'

def test_ad_dry_yield_uses_moisture(repo):
    request = CalculationInput('Food and organic waste', 'EBMUD food waste pulp', 100, moisture_pct=90, desired_output='biogas', parameter_id='P0001', reference_mode=True)
    result = calculate(request, 'Anaerobic digestion', repo)
    assert result.intermediate_products[0]['value'] == pytest.approx(4.2)
    assert result.calculated_value is None
    assert not calculate(replace(request, moisture_pct=None), 'Anaerobic digestion', repo).intermediate_products

def test_char_not_certified_biochar(repo, wood):
    result = calculate(replace(wood, desired_output='biochar', parameter_id='P0023'), 'Pyrolysis', repo)
    assert result.calculated_value is None
    assert result.intermediate_products[0]['value'] == pytest.approx(10.8)

def test_feed_chemical_energy_not_heat_or_electricity(repo):
    request = CalculationInput('Municipal solid waste', 'Dry shredded garbage sample A', 100, moisture_pct=0, desired_output='solid fuel energy', reference_mode=True)
    result = calculate(request, 'Combustion', repo)
    assert result.calculated_value == 1850
    assert result.gross_vs_net_classification == 'theoretical_chemical_energy'
    assert calculate(replace(request, desired_output='electricity'), 'Combustion', repo).calculated_value is None

def test_no_industrial_efficiency_applied_to_small_mass(repo):
    request = CalculationInput('Food and organic waste', 'Biogas from food waste digestion', 1, 'g', desired_output='electricity', reference_mode=True)
    result = calculate(request, 'Combined heat and power', repo)
    assert result.calculated_value is None
    assert any('scale' in m for m in result.missing_parameters)

def test_documented_food_to_biogas_to_chp_chain_stays_incomplete(repo):
    request = CalculationInput('Food and organic waste', 'Source-separated food waste', 100, desired_output='electricity')
    result = recommend(request, repo)
    assert not result['recommendations']
    assert result['alternatives'][0]['technology'] == 'Combined heat and power'
    assert result['alternatives'][0]['calculation_status'] == 'INSUFFICIENT_DATA'

def test_gross_vs_net_accounting():
    assert electricity_from_fuel(360, 25) == {'value': 25, 'unit': 'kWh', 'classification': 'gross_electricity'}
    assert electricity_from_fuel(360, 25, auxiliary_kwh=5)['value'] == 20
    assert electricity_from_fuel(360, 25, auxiliary_kwh=5)['classification'] == 'net_electricity'
    assert electricity_from_fuel(360, 25, efficiency_is_net=True)['classification'] == 'equipment_net_electricity'
    with pytest.raises(ValueError):
        electricity_from_fuel(360, 25, auxiliary_kwh=5, efficiency_is_net=True)

def test_mapping_and_inert_exclusion(repo):
    assert [r['technology'] for r in repo.applicable_technologies('Used cooking oil and fats', 'Yellow grease')] == ['Biodiesel production']
    assert repo.applicable_technologies('Inert waste', 'Glass') == []
    assert repo.applicable_technologies('Plastics', 'PVC') == []

def test_restricted_hazardous_never_recommended(repo):
    request = CalculationInput('Hazardous and medical waste', 'Regulated medical waste', 100, desired_output='electricity', technology_preference='Combustion')
    result = recommend(request, repo)
    assert result['recommendations'] == []
    assert result['alternatives'][0]['calculation_status'] == 'RESTRICTED'

def test_preference_does_not_override_compatibility(repo, wood):
    result = recommend(replace(wood, technology_preference='Biodiesel production'), repo)
    assert not result['recommendations']
    assert result['alternatives'][0]['calculation_status'] == 'NOT_APPLICABLE'

def test_operating_forecast_requires_scale_validation(repo, wood):
    assert calculate(replace(wood, reference_mode=False), 'Pyrolysis', repo).calculated_value is None

def test_no_double_counting(repo):
    request = CalculationInput('Agricultural residues', 'Corn stover', 100, desired_output='ethanol')
    result = recommend(request, repo)
    assert result['allocation']['combined_output'] is None
    assert result['allocation']['mode'] == 'mutually_exclusive_alternatives'

@pytest.mark.parametrize('category,subtype,output,technology', [
    ('Agricultural residues', 'Corn stover', 'ethanol', 'Fermentation'),
    ('Used cooking oil and fats', 'Yellow grease', 'biodiesel', 'Biodiesel production'),
    ('Sewage sludge', 'Detroit 50/50 primary/secondary sludge; WW06 SS-2', 'bio-oil', 'Hydrothermal conversion'),
    ('Municipal solid waste', 'Combustible RDF fraction', 'solid fuel energy', 'RDF/SRF production'),
    ('Landfill waste', 'Biodegradable waste already in MSW landfill', 'biogas', 'Landfill gas recovery'),
    ('Industrial waste heat', 'Industrial hot gases and liquids', 'useful heat', 'Industrial waste heat recovery'),
])
def test_missing_pathways_explicit(repo, category, subtype, output, technology):
    result = calculate(CalculationInput(category, subtype, 100, desired_output=output), technology, repo)
    assert result.calculation_status == 'INSUFFICIENT_DATA'
    assert result.missing_parameters and result.calculated_value is None

def test_invalid_requests(repo, wood):
    with pytest.raises(ValueError):
        replace(wood, desired_output='magic energy')
    with pytest.raises(ValueError):
        recommend(replace(wood, waste_category='Unknown'), repo)
    with pytest.raises(ValueError):
        recommend(replace(wood, technology_preference='Unknown'), repo)

def test_cli_json():
    command = [sys.executable, str(ROOT/'scripts/demo_calculation.py'), '--examples']
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert len(json.loads(result.stdout)) == 17

def test_datasets_unchanged(repo):
    assert repo.unchanged()
    before = json.loads((ROOT/'reports/phase2_dataset_hashes_before.json').read_text())
    # Accommodate the initial inspection's filename-keyed hash manifest.
    for name, digest in repo.hashes.items():
        assert digest == before.get(name, before.get(name+'.csv'))
