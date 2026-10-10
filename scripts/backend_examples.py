"""Capture actual API examples and verify the pre-implementation CSV hashes."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
from backend.main import app


def main():
    wood = dict(waste_category='Wood and forestry waste', waste_subtype='Dry wood reference',
                quantity_kg=100, moisture_pct=10, technology='Pyrolysis', desired_output='bio-oil',
                parameter_id='P0022', reference_mode=True)
    requests = [wood, {**wood, 'reference_mode': False},
                {**wood, 'desired_output': 'electricity'},
                {**wood, 'technology': 'Gasification', 'desired_output': 'syngas',
                 'waste_subtype': 'Wood chips, Walawender 1985 run 98',
                 'parameter_id': 'P0056', 'moisture_pct': 16.52}]
    with TestClient(app) as client:
        examples = []
        for body in requests:
            response = client.post('/api/calculate', json=body)
            response.raise_for_status()
            examples.append(dict(request=body, http_status=response.status_code, response=response.json()))
        (ROOT / 'reports/backend_examples.json').write_text(json.dumps(examples, indent=2, allow_nan=False), encoding='utf-8')
        (ROOT / 'reports/backend_catalog.json').write_text(json.dumps({
            'wastes': client.get('/api/wastes').json(),
            'technologies': client.get('/api/technologies').json()}, indent=2), encoding='utf-8')
    before = json.loads((ROOT / 'reports/backend_dataset_hashes_before.json').read_text())
    after = {n: hashlib.sha256((ROOT / 'data' / (n + '.csv')).read_bytes()).hexdigest() for n in before}
    (ROOT / 'reports/backend_dataset_hashes_after.json').write_text(json.dumps(after, indent=2), encoding='utf-8')
    if before != after:
        raise RuntimeError('Scientific CSV hash mismatch')
    print('Captured 4 actual API examples; all six scientific CSV hashes unchanged.')


if __name__ == '__main__':
    main()
