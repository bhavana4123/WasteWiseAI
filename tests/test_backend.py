"""HTTP contract and scientific boundary integration checks."""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient
from backend.main import app, repository
from engine import DataRepository
from engine.recommender import OUTPUT_ROUTES

ROOT = Path(__file__).resolve().parents[1]
WOOD = dict(waste_category='Wood and forestry waste', waste_subtype='Dry wood reference',
            quantity_kg=100, moisture_pct=10, technology='Pyrolysis', desired_output='bio-oil',
            parameter_id='P0022', reference_mode=True)


@pytest.fixture(scope='module')
def client():
    with TestClient(app) as client:
        yield client


def test_health_catalogs_and_docs(client):
    health = client.get('/api/health').json()
    assert health['status'] == 'ok'
    assert health['scientific_validation'] == 'FAILED_SOURCE_RECONCILIATION'
    assert health['external_predictive_validation'] == 'NOT_VALIDATED'
    assert health['electricity_heat_forecasts'] == 'BLOCKED'
    repo = DataRepository()
    expected = {(r['waste_category'], r['waste_subtype']) for n in
                ['waste_properties', 'technology_mapping'] for r in repo.tables[n]}
    for subtype in {r['waste_subtype'] for r in repo.tables['conversion_parameters']}:
        for category in {c for c, s in expected.copy()}:
            if repo.applicable_technologies(category, subtype):
                expected.add((category, subtype))
    catalog = client.get('/api/wastes').json()['categories']
    assert {(r['waste_category'], s) for r in catalog for s in r['subtypes']} == expected
    technologies = client.get('/api/technologies').json()['technologies']
    assert {t['technology'] for t in technologies} == set(OUTPUT_ROUTES)
    for t in technologies:
        response = client.get('/api/technologies/' + quote(t['technology'], safe=''))
        assert response.status_code == 200
        assert response.json()['mappings']
        assert response.json()['equipment_forecast_supported'] is False
    assert client.get('/api/technologies/unknown').status_code == 404
    assert client.get('/docs').status_code == 200
    schema = client.get('/openapi.json').json()
    assert '/api/calculate' in schema['paths']


def test_reference_and_default_mode(client):
    response = client.post('/api/calculate', json=WOOD)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['calculation_status'] == 'CALCULATED_REFERENCE'
    assert result['calculated_value'] == 67.5
    assert result['unit'] == 'kg liquid pyrolysis product including water'
    assert result['input_waste_details']['mass_kg'] == 100
    assert result['source_references'][0]['source_id'] == 'S07'
    assert result['formula'] and result['evidence']
    assert isinstance(result['intermediate_products'], list)
    blocked = client.post('/api/calculate', json={**WOOD, 'reference_mode': False}).json()
    assert blocked['calculation_status'] == 'INSUFFICIENT_DATA'
    assert blocked['calculated_value'] is None


@pytest.mark.parametrize('field,value', [
    ('quantity_kg', -1), ('quantity_kg', 0), ('quantity_kg', True), ('quantity_kg', '100'),
    ('moisture_pct', -1), ('moisture_pct', 101), ('moisture_pct', True),
    ('waste_category', 'unknown'), ('waste_subtype', 'unknown'), ('technology', 'unknown'),
    ('desired_output', 'unknown'), ('reference_mode', 'true'), ('property_id', 'W0046'),
])
def test_invalid_requests(client, field, value):
    response = client.post('/api/calculate', json={**WOOD, field: value})
    assert response.status_code == 422, response.text
    assert response.json()['code'] == 'INVALID_REQUEST'


@pytest.mark.parametrize('field', ['quantity_kg', 'moisture_pct'])
@pytest.mark.parametrize('token', ['NaN', 'Infinity', '-Infinity', '1e999'])
def test_nonfinite_json(client, field, token):
    body = json.dumps({**WOOD, field: 'TOKEN'}).replace('"TOKEN"', token)
    response = client.post('/api/calculate', content=body, headers={'Content-Type': 'application/json'})
    assert response.status_code == 422
    assert 'code' in response.json()


def test_malformed_and_extra_fields(client):
    assert client.post('/api/calculate', content='{', headers={'Content-Type': 'application/json'}).status_code == 422
    assert client.post('/api/calculate', json={**WOOD, 'efficiency': 99}).status_code == 422


def test_gas_reference_and_unknown_moisture_feasibility(client):
    body = {**WOOD, 'waste_subtype': 'Wood chips, Walawender 1985 run 98', 'technology': 'Gasification',
            'moisture_pct': 16.52, 'desired_output': 'syngas', 'parameter_id': 'P0056'}
    response = client.post('/api/calculate', json=body)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['calculated_value'] == pytest.approx(185.3256)
    assert result['feasibility_checks']['moisture_feasibility']['status'] == 'UNKNOWN'
    assert 'Nm3' not in result['unit']
    mismatch = client.post('/api/calculate', json={**body, 'moisture_pct': 5}).json()
    assert mismatch['calculated_value'] is None


@pytest.mark.parametrize('output', ['electricity', 'useful heat'])
def test_all_documented_energy_routes_blocked(client, output):
    repo = DataRepository()
    for mapping in repo.tables['technology_mapping']:
        response = client.post('/api/calculate', json=dict(
            waste_category=mapping['waste_category'], waste_subtype=mapping['waste_subtype'],
            quantity_kg=100, moisture_pct=10, technology=mapping['technology'],
            desired_output=output, reference_mode=True))
        assert response.status_code == 200, response.text
        result = response.json()
        assert result['calculated_value'] is None
        assert result['calculation_status'] != 'CALCULATED_REFERENCE'


def test_unknown_moisture_ambiguous_study_and_overflow(client):
    for update in [{'moisture_pct': None}, {'parameter_id': None}, {'quantity_kg': 1e308, 'desired_output': 'electricity'}]:
        result = client.post('/api/calculate', json={**WOOD, **update}).json()
        assert result['calculated_value'] is None
        assert result['missing_parameters']


def test_cors(client):
    headers = {'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'POST',
               'Access-Control-Request-Headers': 'content-type'}
    response = client.options('/api/calculate', headers=headers)
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == headers['Origin']
    assert client.options('/api/calculate', headers={**headers, 'Origin': 'https://unknown.example'}).status_code == 400


def test_integrity_and_service_failure(client):
    class Changed:
        def unchanged(self):
            return False
    original = app.state.repository
    app.state.repository = Changed()
    try:
        response = client.post('/api/calculate', json=WOOD)
        assert response.status_code == 503
    finally:
        app.state.repository = original
    def broken():
        raise RuntimeError('private internal detail')
    app.dependency_overrides[repository] = broken
    try:
        with TestClient(app, raise_server_exceptions=False) as safe_client:
            response = safe_client.post('/api/calculate', json=WOOD)
            assert response.status_code == 500
            assert 'private internal detail' not in response.text
    finally:
        app.dependency_overrides.clear()


def test_original_csv_hashes():
    baseline = json.loads((ROOT / 'reports/backend_dataset_hashes_before.json').read_text())
    historical = json.loads((ROOT / 'reports/independent_hashes_after.json').read_text())
    for name, digest in baseline.items():
        assert hashlib.sha256((ROOT / 'data' / (name + '.csv')).read_bytes()).hexdigest() == digest
    # The original audit also retained the same six dataset hashes.
    assert set(baseline.values()).issubset(set(historical.values()))


@pytest.mark.parametrize('category,subtype,expected', [
    ('Wood and forestry waste', 'Dry wood reference', {'Pyrolysis'}),
    ('Wood and forestry waste', 'Wood chips, Walawender 1985 run 98', {'Gasification'}),
    ('Food and organic waste', 'Source-separated food waste', {'Anaerobic digestion', 'Combined heat and power'}),
    ('Agricultural residues', 'Rice straw after harvest', set()),
    ('Paper and cardboard', 'Newsprint', set()),
    ('Plastics', 'Commercial reference polymer PP-1', set()),
    ('Agricultural residues', 'Corn stover', {'Fermentation'}),
])
def test_pathways_match_engine_exact_verified_scopes(client, category, subtype, expected):
    response = client.get('/api/pathways', params={'waste_category': category, 'waste_subtype': subtype})
    assert response.status_code == 200, response.text
    rows = response.json()['pathways']
    assert {p['technology'] for p in rows if p['default_eligible']} == expected
    repo = DataRepository()
    assert {m['technology'] for m in repo.applicable_technologies(category, subtype) if m['feasibility_status'] != 'restricted'} == expected
    for p in rows:
        if p['mapping_status'] == 'VERIFIED':
            assert p['mapping_records'] and p['source_references']
            assert p['calculation_support'] == 'EVIDENCE_GATED'
        else:
            assert p['calculation_support'] == 'UNSUPPORTED'
            assert p['feasibility_status'] == 'not_established'
        assert p['blocked_forecasts'] == sorted(set(p['requested_outputs']) & {'electricity', 'useful heat'})


def test_restricted_pathway_never_default_eligible(client):
    response = client.get('/api/pathways', params={'waste_category': 'Hazardous and medical waste', 'waste_subtype': 'Regulated medical waste'})
    combustion = next(p for p in response.json()['pathways'] if p['technology'] == 'Combustion')
    assert combustion['mapping_status'] == 'RESTRICTED'
    assert combustion['calculation_support'] == 'RESTRICTED'
    assert not combustion['default_eligible']


def test_unknown_pathway_feed_rejected(client):
    response = client.get('/api/pathways', params={'waste_category': 'Agricultural residues', 'waste_subtype': 'Dry wood reference'})
    assert response.status_code == 422


def test_pathway_catalog_cannot_skip_evidence_gate(client, monkeypatch):
    # A cached name cannot confer verification on its mapping.
    assert client.get('/api/wastes').status_code == 200
    monkeypatch.setattr(DataRepository, 'verified_field', lambda *args: False)
    response = client.get('/api/pathways', params={'waste_category': 'Wood and forestry waste', 'waste_subtype': 'Dry wood reference'})
    assert response.status_code == 200
    assert not any(p['default_eligible'] for p in response.json()['pathways'])
    assert all(p['mapping_status'] == 'UNKNOWN' for p in response.json()['pathways'])


@pytest.mark.parametrize('category,subtype,technology,output', [
    ('Wood and forestry waste', 'Dry wood reference', 'Pyrolysis', 'bio-oil'),
    ('Wood and forestry waste', 'Wood chips, Walawender 1985 run 98', 'Gasification', 'syngas'),
    ('Food and organic waste', 'Source-separated food waste', 'Anaerobic digestion', 'biogas'),
    ('Food and organic waste', 'EBMUD food waste pulp', 'Anaerobic digestion', 'biogas'),
    ('Municipal solid waste', 'Dry shredded garbage sample A', 'Combustion', 'solid fuel energy'),
    ('Agricultural residues', 'Corn stover', 'Fermentation', 'ethanol'),
])
def test_automatic_recommendation_exact_feed_and_unblocked_output(client, category, subtype, technology, output):
    response = client.get('/api/pathways', params={'waste_category': category, 'waste_subtype': subtype})
    assert response.status_code == 200, response.text
    eligible = [p for p in response.json()['pathways'] if p['default_eligible'] and p['recommended_output']]
    assert eligible[0]['technology'] == technology
    assert eligible[0]['recommended_output'] == output
    assert all(p['recommended_output'] not in {'electricity', 'useful heat'} for p in response.json()['pathways'])
    assert all(p['recommended_output'] is None for p in response.json()['pathways'] if not p['default_eligible'])


def test_recommendation_parameters_do_not_silently_choose_a_study(client):
    rows = client.get('/api/pathways', params={'waste_category': 'Wood and forestry waste', 'waste_subtype': 'Dry wood reference'}).json()['pathways']
    oil = next(a for p in rows if p['technology'] == 'Pyrolysis' for a in p['output_assessments'] if a['output'] == 'bio-oil')
    assert oil['matching_parameter_ids'] == ['P0022', 'P0025', 'P0028']
    assert oil['study_selection_required'] and oil['has_verified_parameters']
    assert oil['calculation_status'] == 'INSUFFICIENT_DATA'
    assert 'calculated_value' not in oil


def test_parameter_evidence_loss_does_not_approve_recommendation(client, monkeypatch):
    original = DataRepository.verified_field
    def verified(self, table, row, field):
        return False if table == 'conversion_parameters' else original(self, table, row, field)
    monkeypatch.setattr(DataRepository, 'verified_field', verified)
    pathways = client.get('/api/pathways', params={'waste_category': 'Wood and forestry waste', 'waste_subtype': 'Dry wood reference'}).json()['pathways']
    pyrolysis = next(p for p in pathways if p['technology'] == 'Pyrolysis')
    assert pyrolysis['mapping_status'] == 'VERIFIED'
    assert not any(a['has_verified_parameters'] for a in pyrolysis['output_assessments'])


TIMBER_STUDIES = dict(waste_category='Wood and forestry waste', waste_subtype='Dry wood reference', technology='Pyrolysis', desired_output='bio-oil')


def test_timber_studies_are_output_specific_verified_and_have_no_moisture_default(client):
    response = client.get('/api/reference-studies', params=TIMBER_STUDIES)
    assert response.status_code == 200, response.text
    data = response.json()
    assert [s['parameter']['parameter_id'] for s in data['studies']] == ['P0022', 'P0025', 'P0028']
    assert [s['parameter']['value_typical'] for s in data['studies']] == ['75', '50', '30']
    assert all(s['selectable'] and s['evidence_status'] == 'VERIFIED' for s in data['studies'])
    assert all(s['parameter']['measurement_basis'] == 'dry wood mass' and s['parameter']['unit'] == '% dry feed mass' for s in data['studies'])
    assert all(s['source_reference']['source_id'] == 'S07' and s['evidence'] for s in data['studies'])
    assert data['reference_samples'] == []
    assert 'does not imply zero moisture' in data['moisture_explanation']
    assert 'not an energy forecast' in data['required_acknowledgement']


def test_study_yield_evidence_loss_disables_selection(client, monkeypatch):
    original = DataRepository.verified_field
    monkeypatch.setattr(DataRepository, 'verified_field', lambda self, table, row, field: False if table == 'conversion_parameters' else original(self, table, row, field))
    studies = client.get('/api/reference-studies', params=TIMBER_STUDIES).json()['studies']
    assert len(studies) == 3
    assert all(s['evidence_status'] == 'UNKNOWN' and not s['selectable'] for s in studies)


@pytest.mark.parametrize('parameter,expected', [('P0022', 67.5), ('P0025', 45), ('P0028', 27)])
def test_published_timber_modes_mass_basis_sources_and_scaling(client, parameter, expected):
    for mass, multiplier in [(100, 1), (200, 2)]:
        response = client.post('/api/calculate', json={**WOOD, 'parameter_id': parameter, 'quantity_kg': mass})
        assert response.status_code == 200
        data = response.json()
        assert data['scenario_id'] == parameter and data['calculation_status'] == 'CALCULATED_REFERENCE'
        assert data['calculated_value'] == pytest.approx(expected * multiplier)
        assert data['unit'] == 'kg liquid pyrolysis product including water'
        assert data['formula'] == 'wet_mass_kg*(1-moisture_pct/100)*product_mass_yield_pct/100'
        assert data['gross_vs_net_classification'] == 'intermediate_product_quantity'
        assert data['input_waste_details']['property_id'] is None
        assert data['input_waste_details']['moisture_pct'] == 10
        assert any(p.get('measurement_basis') == 'dry wood mass' for p in data['parameters'])
        assert any(s['source_id'] == 'S07' and s['publication_title'] == 'IEA Bioenergy Annual Report 2006' for s in data['source_references'])


def test_timber_missing_moisture_never_defaults_to_dry_feed(client):
    data = client.post('/api/calculate', json={**WOOD, 'moisture_pct': None}).json()
    assert data['calculation_status'] == 'INSUFFICIENT_DATA' and data['calculated_value'] is None
    assert any('moisture' in p for p in data['missing_parameters'])


@pytest.mark.parametrize('override', [{'waste_category': 'Agricultural residues'}, {'technology': 'invented'}, {'desired_output': 'biogas'}])
def test_reference_studies_reject_mismatched_or_unknown_requests(client, override):
    assert client.get('/api/reference-studies', params={**TIMBER_STUDIES, **override}).status_code == 422


GAS_RUN98 = dict(waste_category='Wood and forestry waste', waste_subtype='Wood chips, Walawender 1985 run 98', technology='Gasification', desired_output='syngas')


def test_gasification_guided_study_uses_verified_run_observation(client):
    response = client.get('/api/reference-studies', params=GAS_RUN98)
    assert response.status_code == 200, response.text
    data = response.json()
    assert [s['parameter']['parameter_id'] for s in data['studies']] == ['P0056']
    assert data['studies'][0]['selectable'] and data['studies'][0]['source_reference']['source_id'] == 'S02'
    assert data['reference_run_moisture']['value'] == 16.52
    assert data['reference_run_moisture']['kind'] == 'published_point_observation_not_equipment_limit'
    assert data['reference_samples'] == []
    assert 'not Nm3' in data['required_acknowledgement']


def test_gasification_guided_quantity_and_paired_energy_scale_without_normalization(client):
    for mass,multiplier in [(100,1),(200,2)]:
        data = client.post('/api/calculate',json={**GAS_RUN98,'quantity_kg':mass,'moisture_pct':16.52,'parameter_id':'P0056','reference_mode':True}).json()
        assert data['calculation_status']=='CALCULATED_REFERENCE'
        assert data['calculated_value']==pytest.approx(185.3256*multiplier)
        assert data['unit']=='m3 dry producer gas (source T/P unspecified)'
        assert data['gross_vs_net_classification']=='intermediate_product_quantity'
        energy=next(p for p in data['intermediate_products'] if p['name']=='recoverable_producer_gas_chemical_energy_reference')
        assert energy['value']==pytest.approx(987.785448*multiplier) and energy['unit']=='MJ HHV'
        assert energy['classification']=='recoverable_fuel_energy'
        assert data['feasibility_checks']['moisture_feasibility']['status']=='UNKNOWN'
        assert {p.get('record_id') for p in data['parameters']} >= {'P0056','P0055'}
        assert data['source_ids']==['S02']


def test_gasification_guided_mismatched_moisture_blocks_all_quantities(client):
    data=client.post('/api/calculate',json={**GAS_RUN98,'quantity_kg':100,'moisture_pct':17,'parameter_id':'P0056','reference_mode':True}).json()
    assert data['calculation_status']=='INSUFFICIENT_DATA' and data['calculated_value'] is None
    assert data['intermediate_products']==[]
    assert any('matching the selected gasification run' in gap for gap in data['missing_parameters'])
