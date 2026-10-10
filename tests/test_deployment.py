"""Production startup, origin isolation and working-directory independence."""
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from backend.settings import cors_origins, runtime_port


def test_port_default_and_override(monkeypatch):
    monkeypatch.delenv('PORT', raising=False)
    assert runtime_port() == 8080
    monkeypatch.setenv('PORT', '9090')
    from backend.__main__ import main
    with patch('backend.__main__.uvicorn.run') as run:
        main()
    run.assert_called_once_with('backend.main:app', host='0.0.0.0', port=9090)


@pytest.mark.parametrize('value', ['0', '65536', '-1', 'abc', '8080.0', ''])
def test_invalid_port(monkeypatch, value):
    monkeypatch.setenv('PORT', value)
    with pytest.raises(ValueError, match='PORT'):
        runtime_port()


def test_production_defaults_deny_cross_origin(monkeypatch):
    monkeypatch.setenv('WASTEWISE_ENV', 'production')
    monkeypatch.delenv('WASTEWISE_CORS_ORIGINS', raising=False)
    assert cors_origins() == []


@pytest.mark.parametrize('value', ['*', 'https://*.example.com', 'null',
    'https://site.example.com/path', 'https://site.example.com/',
    'https://user:password@site.example.com', 'https://site.example.com?x=1',
    'https://site.example.com#fragment', 'ftp://site.example.com',
    'https://site.example.com:invalid'])
def test_unsafe_origins_rejected(monkeypatch, value):
    monkeypatch.setenv('WASTEWISE_CORS_ORIGINS', value)
    with pytest.raises(ValueError):
        cors_origins()


def test_production_health_and_cors_outside_repository(tmp_path):
    root = Path(__file__).resolve().parents[1]
    code = '''
from fastapi.testclient import TestClient
from backend.main import app
with TestClient(app) as client:
    health = client.get('/api/health')
    assert health.status_code == 200
    assert health.json()['status'] == 'ok'
    assert health.json()['datasets_unchanged_since_startup'] is True
    assert health.json()['electricity_heat_forecasts'] == 'BLOCKED'
    allowed = client.options('/api/calculate', headers={
        'Origin': 'https://frontend.example.com',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type'})
    assert allowed.status_code == 200
    assert allowed.headers['access-control-allow-origin'] == 'https://frontend.example.com'
    assert 'access-control-allow-credentials' not in allowed.headers
    denied = client.options('/api/calculate', headers={
        'Origin': 'https://attacker.example.com',
        'Access-Control-Request-Method': 'POST'})
    assert denied.status_code == 400
    assert 'access-control-allow-origin' not in denied.headers
'''
    env = dict(os.environ, PYTHONPATH=str(root), WASTEWISE_ENV='production',
               WASTEWISE_CORS_ORIGINS='https://frontend.example.com')
    subprocess.run([sys.executable, '-c', code], cwd=tmp_path, env=env,
                   check=True, capture_output=True, text=True)
