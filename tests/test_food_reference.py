"""Independent basis arithmetic and HTTP regressions for the one food reference."""
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from engine import CalculationInput, DataRepository
from engine.recommender import calculate
from engine.food_reference import FOOD_SUBTYPE

FOOD = dict(waste_category='Food and organic waste', waste_subtype=FOOD_SUBTYPE,
            quantity_kg=100, moisture_pct=93.6, technology='Anaerobic digestion',
            desired_output='biogas', parameter_id='P0006', reference_mode=True)

@pytest.fixture(scope='module')
def client():
    with TestClient(app) as value:
        yield value


def expected_volume(mass=100):
    # Independent decimal dimensional accounting; VS fractions are not wet fractions.
    D = Decimal
    vs_kg = D(str(mass)) * D('0.064') * D('0.863')
    kg_vs_per_m3_day = D('0.22') * D('0.45359237') / D('0.028316846592')
    return float(vs_kg / (kg_vs_per_m3_day * D('0.030')) * D('0.096'))

@pytest.mark.parametrize('mass', [80, 100, 200, 0.0001])
def test_food_actual_api_wet_ts_vs_basis_and_distinct_gas_species(client, mass):
    response = client.post('/api/calculate', json={**FOOD, 'quantity_kg': mass})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['calculation_status'] == 'CALCULATED_REFERENCE'
    assert body['calculated_value'] == pytest.approx(expected_volume(mass), rel=1e-12)
    assert body['unit'] == 'm3 biogas (source T/P unspecified)'
    products = {p['name']: p for p in body['intermediate_products']}
    assert products['reference_total_solids_mass']['value'] == pytest.approx(mass * .064)
    assert products['reference_volatile_solids_mass']['value'] == pytest.approx(mass * .064 * .863)
    assert products['raw_methane_in_digester_gas']['value'] == pytest.approx(expected_volume(mass) * .64)
    assert products['raw_methane_in_digester_gas']['unit'].startswith('m3 CH4')
    assert products['reference_methane_fraction']['value'] == 64
    assert body['feasibility_checks']['gas_chemical_energy']['value'] is None
    assert body['feasibility_checks']['moisture_feasibility']['status'] == 'UNKNOWN'
    assert not any(p.get('unit', '').startswith(('MJ', 'kWh')) for p in products.values())
    assert {p.get('record_id') for p in body['parameters']} >= {'P0006', 'P0007', 'P0009', 'W0059', 'T0012'}
    assert 'S03' in body['source_ids']
    assert '0.45359237' in body['formula']
    assert any('ratio' in text.lower() for text in body['assumptions'])
    assert body['uncertainty']['statistical'].startswith('No uncertainty interval')

@pytest.mark.parametrize('override', [
    {'reference_mode': False}, {'parameter_id': None}, {'parameter_id': 'P0001'},
    {'parameter_id': 'P0010'}, {'moisture_pct': None}, {'moisture_pct': 93.5},
    {'desired_output': 'biomethane'}, {'desired_output': 'electricity'},
    {'desired_output': 'useful heat'},
])
def test_food_missing_basis_foreign_study_and_forecasts_are_blocked(client, override):
    body = client.post('/api/calculate', json={**FOOD, **override}).json()
    assert body['calculation_status'] != 'CALCULATED_REFERENCE'
    assert body['calculated_value'] is None
    assert body['missing_parameters']


def test_food_no_implicit_reference_sample_but_explicit_sample_is_supported(client):
    unknown = client.post('/api/calculate', json={**FOOD, 'moisture_pct': None}).json()
    assert unknown['calculated_value'] is None
    exact = client.post('/api/calculate', json={**FOOD, 'moisture_pct': None, 'property_id': 'W0059'}).json()
    assert exact['calculated_value'] == pytest.approx(expected_volume())
    assert client.post('/api/calculate', json={**FOOD, 'property_id': 'W0057'}).status_code == 422


def test_food_guide_one_matching_study_and_all_linked_evidence(client):
    body = client.get('/api/reference-studies', params={k: FOOD[k] for k in
        ['waste_category', 'waste_subtype', 'technology', 'desired_output']}).json()
    assert [(s['parameter']['parameter_id'], s['selectable']) for s in body['studies']] == [('P0006', True)]
    assert body['reference_run_moisture']['value'] == 93.6
    assert body['reference_run_moisture']['record_id'] == 'W0059'
    assert [s['property_id'] for s in body['reference_samples']] == ['W0059']
    assert len(body['linked_reference_parameters']) == 7
    assert 'ratio-of-published-means' in body['required_acknowledgement']
    assert 'not raw delivered' in body['moisture_explanation']

@pytest.mark.parametrize('identifier,field', [
    ('P0006', 'value_typical'), ('P0007', 'value_typical'), ('P0009', 'value_typical'),
    ('W0059', 'total_solids_pct'), ('W0059', 'volatile_solids_pct_ts'),
    ('T0012', 'capacity'), ('T0012', 'operating_temperature_c'),
])
def test_every_unverified_dependency_blocks_the_entire_food_calculation(identifier, field, monkeypatch):
    repo = DataRepository()
    original = repo.verified_field
    monkeypatch.setattr(repo, 'verified_field', lambda table, row, requested:
        False if row['record_id'] == identifier and requested == field else original(table, row, requested))
    request = CalculationInput(FOOD['waste_category'], FOOD_SUBTYPE, 100, moisture_pct=93.6,
        desired_output='biogas', parameter_id='P0006', reference_mode=True)
    result = calculate(request, 'Anaerobic digestion', repo)
    assert result.calculated_value is None and result.intermediate_products == []
    assert result.feasibility_checks['reference_bundle']['status'] == 'UNKNOWN'

@pytest.mark.parametrize('identifier,field,value', [
    ('P0007', 'operating_conditions', 'thermophilic; 15-day MCRT'),
    ('P0009', 'measurement_basis', 'volatile solids destroyed'),
    ('P0006', 'unit', 'L CH4/h'),
    ('T0012', 'capacity_unit', 'kg/day'),
])
def test_food_cannot_mix_conditions_species_or_volume_and_mass_bases(identifier, field, value):
    repo = DataRepository()
    for rows in repo.tables.values():
        for row in rows:
            if row.get('record_id') == identifier and field in row:
                row[field] = value
    request = CalculationInput(FOOD['waste_category'], FOOD_SUBTYPE, 100, moisture_pct=93.6,
        desired_output='biogas', parameter_id='P0006', reference_mode=True)
    result = calculate(request, 'Anaerobic digestion', repo)
    assert result.calculated_value is None and not result.intermediate_products


def test_food_extreme_but_finite_reference_quantity_is_not_arbitrarily_capped(client):
    body = client.post('/api/calculate', json={**FOOD, 'quantity_kg': 1e308}).json()
    # The reference has a sub-unity wet-mass coefficient; a finite result is allowed.
    assert body['calculation_status'] == 'CALCULATED_REFERENCE'
    assert body['calculated_value'] == pytest.approx(expected_volume(1e308), rel=1e-12)


def test_food_underflow_discards_partial_quantities_instead_of_inventing_zero(client):
    body = client.post('/api/calculate', json={**FOOD, 'quantity_kg': 5e-324}).json()
    assert body['calculation_status'] == 'INSUFFICIENT_DATA'
    assert body['calculated_value'] is None and body['intermediate_products'] == []
    assert body['errors'][0]['code'] == 'NUMERIC_UNDERFLOW'


def test_food_guide_disables_study_when_linked_vs_evidence_is_unverified(client, monkeypatch):
    original = DataRepository.verified_field
    monkeypatch.setattr(DataRepository, 'verified_field', lambda self, table, row, field:
        False if row['record_id'] == 'W0059' and field == 'volatile_solids_pct_ts'
        else original(self, table, row, field))
    body = client.get('/api/reference-studies', params={k: FOOD[k] for k in
        ['waste_category', 'waste_subtype', 'technology', 'desired_output']}).json()
    assert body['studies'][0]['selectable'] is False
    assert body['studies'][0]['evidence_status'] == 'UNKNOWN'
    assert body['reference_samples'] == []
    assert body['linked_reference_parameters'] == []
    assert body['reference_run_moisture'] is None
