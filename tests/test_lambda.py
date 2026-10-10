"""Real Mangum event integration; never substitutes a mock adapter."""
import base64
import json
from types import SimpleNamespace

import pytest

WOOD = dict(waste_category='Wood and forestry waste', waste_subtype='Dry wood reference',
            quantity_kg=100, moisture_pct=10, technology='Pyrolysis', desired_output='bio-oil',
            parameter_id='P0022', reference_mode=True)
FOOD = dict(waste_category='Food and organic waste',
            waste_subtype='EBMUD food waste pulp; mesophilic; 15-day MCRT', quantity_kg=100,
            moisture_pct=93.6, technology='Anaerobic digestion', desired_output='biogas',
            parameter_id='P0006', reference_mode=True)


def event(path='/api/health', method='GET', payload=None, query='', encoded=False,
          origin=None, domain='example.lambda-url.ap-southeast-2.on.aws'):
    body = json.dumps(payload) if payload is not None else ''
    headers = {'host': domain, 'content-type': 'application/json'}
    if origin:
        headers['origin'] = origin
    if encoded:
        body = base64.b64encode(body.encode()).decode()
    return {
        'version': '2.0', 'routeKey': '$default', 'rawPath': path,
        'rawQueryString': query, 'headers': headers,
        'requestContext': {'accountId': 'test', 'requestId': 'local-test',
            'domainName': domain, 'stage': '$default',
            'http': {'method': method, 'path': path, 'protocol': 'HTTP/1.1',
                     'sourceIp': '127.0.0.1', 'userAgent': 'pytest'}},
        'body': body, 'isBase64Encoded': encoded,
    }


@pytest.fixture
def invoke():
    pytest.importorskip('mangum', reason='Install backend/requirements-lambda.txt to run Lambda integration tests')
    from backend.lambda_handler import handler
    context = SimpleNamespace(aws_request_id='local-test', function_name='wastewise-local',
                              get_remaining_time_in_millis=lambda: 30000)

    def call(**kwargs):
        response = handler(event(**kwargs), context)
        body = response['body']
        if response.get('isBase64Encoded'):
            body = base64.b64decode(body).decode()
        return response, body
    return call


@pytest.mark.parametrize('domain', ['example.lambda-url.ap-southeast-2.on.aws',
                                 'example.execute-api.ap-southeast-2.amazonaws.com'])
def test_lambda_health_function_url_and_http_api(invoke, domain):
    response, body = invoke(domain=domain)
    health = json.loads(body)
    assert response['statusCode'] == 200
    assert health['status'] == 'ok'
    assert health['datasets_unchanged_since_startup'] is True
    assert health['scientific_validation'] == 'FAILED_SOURCE_RECONCILIATION'
    assert health['electricity_heat_forecasts'] == 'BLOCKED'


@pytest.mark.parametrize('path', ['/api/wastes', '/api/technologies', '/openapi.json', '/docs'])
def test_lambda_preserves_catalog_and_docs_routes(invoke, path):
    response, body = invoke(path=path)
    assert response['statusCode'] == 200
    assert body


@pytest.mark.parametrize('encoded', [False, True])
def test_lambda_timber_calculation_and_encoded_post(invoke, encoded):
    response, body = invoke(path='/api/calculate', method='POST', payload=WOOD, encoded=encoded)
    result = json.loads(body)
    assert response['statusCode'] == 200
    assert result['calculated_value'] == 67.5
    assert result['unit'] == 'kg liquid pyrolysis product including water'
    assert result['source_references'][0]['source_id'] == 'S07'
    assert result['formula'] and result['evidence'] and result['limitations']


def test_lambda_food_biogas_is_distinct_from_methane(invoke):
    response, body = invoke(path='/api/calculate', method='POST', payload=FOOD)
    result = json.loads(body)
    assert response['statusCode'] == 200
    assert result['calculated_value'] == pytest.approx(5.01530344515145)
    assert result['unit'] == 'm3 biogas (source T/P unspecified)'
    products = {p['name']: p for p in result['intermediate_products']}
    assert products['raw_methane_in_digester_gas']['value'] == pytest.approx(result['calculated_value'] * .64)
    assert result['feasibility_checks']['gas_chemical_energy']['value'] is None
    assert result['source_references'] and result['evidence']


def test_lambda_gasification_preserves_volume_and_unknown_feasibility(invoke):
    gas = {**WOOD, 'waste_subtype': 'Wood chips, Walawender 1985 run 98',
           'technology': 'Gasification', 'moisture_pct': 16.52,
           'desired_output': 'syngas', 'parameter_id': 'P0056'}
    response, body = invoke(path='/api/calculate', method='POST', payload=gas)
    result = json.loads(body)
    assert response['statusCode'] == 200
    assert result['calculated_value'] == pytest.approx(185.3256)
    assert result['unit'] == 'm3 dry producer gas (source T/P unspecified)'
    assert result['feasibility_checks']['moisture_feasibility']['status'] == 'UNKNOWN'
    assert any(p['name'] == 'recoverable_producer_gas_chemical_energy_reference'
               and p['unit'] == 'MJ HHV' for p in result['intermediate_products'])


@pytest.mark.parametrize('output', ['electricity', 'useful heat'])
def test_lambda_forecasts_remain_blocked(invoke, output):
    response, body = invoke(path='/api/calculate', method='POST',
                            payload={**WOOD, 'desired_output': output})
    assert response['statusCode'] == 200
    assert json.loads(body)['calculated_value'] is None


def test_lambda_input_validation_and_not_found(invoke):
    response, body = invoke(path='/api/calculate', method='POST',
                            payload={**WOOD, 'quantity_kg': -1})
    assert response['statusCode'] == 422
    assert json.loads(body)['code'] == 'INVALID_REQUEST'
    response, body = invoke(path='/api/missing')
    assert response['statusCode'] == 404
    assert json.loads(body)['code'] == 'NOT_FOUND'


def test_lambda_query_parameters_and_warm_health(invoke):
    from urllib.parse import urlencode
    query = urlencode({k: FOOD[k] for k in ('waste_category', 'waste_subtype', 'technology', 'desired_output')})
    response, body = invoke(path='/api/reference-studies', query=query)
    assert response['statusCode'] == 200
    assert json.loads(body)['studies'][0]['parameter']['parameter_id'] == 'P0006'
    first, first_body = invoke()
    second, second_body = invoke()
    assert first['statusCode'] == second['statusCode'] == 200
    assert json.loads(first_body) == json.loads(second_body)


def test_lambda_does_not_bypass_startup_validation(invoke, monkeypatch):
    from backend import main
    def invalid_repository():
        raise ValueError('invalid packaged repository')
    monkeypatch.setattr(main, 'DataRepository', invalid_repository)
    with pytest.raises(Exception):
        invoke()
