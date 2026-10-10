"""Fresh audit retrievals only. Never reads through the production evidence gate.

Publicly accessible sources are saved under reports/independent_evidence. HTTP
failures, redirects and byte hashes remain in a separate audit log.
"""
import csv
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--benchmarks', action='store_true')
    args = parser.parse_args()
    destination = ROOT / 'reports' / 'independent_evidence'
    destination.mkdir(exist_ok=True)
    with (ROOT/'data/sources.csv').open(encoding='utf-8') as handle:
        sources = {r['source_id']: r for r in csv.DictReader(handle)}
    source_ids = ('S01', 'S02', 'S03', 'S07')
    if args.benchmarks:
        sources = {
            'B01': {'source_url': 'https://ris.utwente.nl/ws/portalfiles/portal/288453995/applsci_12_04822_v2.pdf', 'sha256': ''},
            'B02': {'source_url': 'https://mdpi-res.com/d_attachment/processes/processes-08-01407/article_deploy/processes-08-01407.pdf', 'sha256': ''},
            'B03': {'source_url': 'https://mdpi-res.com/d_attachment/environments/environments-05-00084/article_deploy/environments-05-00084.pdf', 'sha256': ''},
        }
        source_ids = tuple(sources)
    log_path = destination / ('benchmark_retrieval_log.json' if args.benchmarks else 'retrieval_log.json')
    log = []
    for source_id in source_ids:
        source = sources[source_id]
        entry = {'source_id': source_id, 'url': source['source_url'], 'access_time_utc': datetime.now(timezone.utc).isoformat(), 'external_verification': 'NOT_CHECKED'}
        try:
            response = requests.get(source['source_url'], timeout=(15, 45), headers={'User-Agent': 'WasteWise-scientific-audit/1.0'}, allow_redirects=True)
            entry.update(http_status=response.status_code, final_url=response.url, content_type=response.headers.get('Content-Type'))
            if response.status_code != 200 or not response.content.startswith(b'%PDF'):
                entry['retrieval_status'] = 'FAILED'
                entry['reason'] = 'HTTP error or response not an original PDF; no access control bypass attempted'
            else:
                path = destination / f'{source_id}_fresh.pdf'
                path.write_bytes(response.content)
                digest = hashlib.sha256(response.content).hexdigest()
                entry.update(retrieval_status='DOWNLOADED', file=str(path.relative_to(ROOT)), sha256=digest, identical_to_archived_bytes=(digest == source['sha256']))
                # Inspection is a separate human/model audit step; download is not verification.
        except requests.RequestException as error:
            entry.update(retrieval_status='FAILED', reason=str(error))
        log.append(entry)
        print(json.dumps(entry), flush=True)
        log_path.write_text(json.dumps(log, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
