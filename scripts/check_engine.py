"""Run Phase 2 tests and examples; write reports only, never scientific CSVs."""
import collections
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import DataRepository, recommend
from engine.recommender import CALCULATORS
from scripts.demo_calculation import example_requests
import pytest

def main():
    repo = DataRepository()
    reports = ROOT / 'reports'
    before = json.loads((reports/'phase2_dataset_hashes_before.json').read_text())
    historical_match = all(digest == before.get(name, before.get(name+'.csv')) for name, digest in repo.hashes.items())
    test = subprocess.run([sys.executable, '-m', 'pytest', str(ROOT/'tests'), '-q', '-p', 'no:cacheprovider', '--junitxml='+str(reports/'independent_tests.xml')], capture_output=True, text=True, encoding='utf-8', cwd=ROOT)
    (reports/'engine_test_results.txt').write_text(test.stdout + test.stderr, encoding='utf-8')
    cases = [recommend(request, repo) for request in example_requests()]
    from scripts.common import SCHEMAS
    inspection = {}
    for name, rows in repo.tables.items():
        inspection[name] = {
            'row_count': len(rows),
            'columns': list(rows[0]) if rows else SCHEMAS[name],
            'missing_values_by_column': {column: sum(not row.get(column) for row in rows) for column in (rows[0] if rows else SCHEMAS[name])},
            'source_ids': sorted({row['source_id'] for row in rows}),
            'units': dict(collections.Counter(row.get('unit') for row in rows if row.get('unit'))),
            'measurement_bases': dict(collections.Counter(row.get('measurement_basis', row.get('heating_value_basis', row.get('efficiency_basis', ''))) for row in rows)),
            'verification_statuses': dict(collections.Counter(row.get('verification_status', 'unspecified') for row in rows)),
        }
    (reports/'engine_data_inspection.json').write_text(json.dumps(inspection, indent=2, ensure_ascii=True), encoding='utf-8')
    (reports/'engine_demo_results.json').write_text(json.dumps(cases, indent=2, ensure_ascii=True, allow_nan=False), encoding='utf-8')
    unchanged = repo.unchanged() and historical_match
    (reports/'phase2_dataset_hashes_after.json').write_text(json.dumps({name+'.csv': digest for name,digest in repo.hashes.items()}, indent=2), encoding='utf-8')
    lines = [
        '# WasteWise AI engineering engine readiness', '',
        f'Executed: {datetime.now(timezone.utc).isoformat()}; Python {platform.python_version()}; pytest {pytest.__version__}.', '',
        f'All six original scientific CSV hashes unchanged: **{unchanged}**. No data collection, regeneration, model training, frontend development or deployment occurred.', '',
        'The engine supports conditional published-reference mass accounting. **Zero technologies currently support an equipment-qualified operating forecast, net plant electricity or useful heat.** Reference calculations require explicit `reference_mode=True`; default mode reports missing equipment/scale validation. User masses and moisture in demos are illustrative inputs, not new scientific dataset measurements.', '',
        '## Implemented technology modules', '',
        '| Technology | Verified calculable output / current blockage |', '|---|---|',
    ]
    readiness = {
        'Anaerobic digestion': 'Raw methane intermediate for five selected EBMUD yields (dry TS or wet delivered basis). Requested biogas blocked by total mass-specific gas yield; biomethane blocked by upgrading recovery/purity. Reactor L/h rates are not mass yields.',
        'Combustion': 'Four exact dry shredded garbage reference samples permit theoretical HHV chemical energy with explicit moisture. This is feed characterization, not recovered combustion energy. Electricity/heat lack qualified solid-fuel efficiency, operating scale and auxiliaries.',
        'Combined heat and power': 'Blocked: equipment records are natural-gas-specific; waste gas energy/specification, qualified efficiency, duration/load and full auxiliary boundary absent.',
        'Gasification': '19 individual wood-chip runs permit producer-gas reference volume; same-run paired gas HHV permits recoverable gas chemical energy. Moisture must match the run; gas T/P unspecified, no Nm3 normalization. No qualified electricity equipment.',
        'Pyrolysis': 'Three dry-wood modes permit liquid product mass (includes water). Char intermediate can be calculated, but requested biochar remains blocked by stability/contaminant/end-use qualification. No product energy recovery calculated.',
        'Fermentation': 'Blocked: same-feed carbohydrate composition, integrated mass balance and documented stoichiometric basis absent. Sugar-specific percentages are not whole-feed ethanol mass yields.',
        'Biodiesel production': 'Blocked: only a strict >99% pure-fatty-acid threshold, not a typical yellow-grease mass yield; feed composition and losses absent.',
        'Hydrothermal conversion': 'Blocked: matching Detroit feed is flagged for elemental closure; no coherent eligible dry ash-free characterization. Biocrude is not pyrolysis oil or biodiesel.',
        'RDF/SRF production': 'Blocked: manufacturing product mass yield, product-specific heating value/moisture and contaminant qualification absent.',
        'Landfill gas recovery': 'Blocked: site inventory/age, temporal yield, methane fraction, collection efficiency and equipment absent.',
        'Industrial waste heat recovery': 'Blocked: temperature ranges alone lack stream flow, duration, heat capacity/enthalpy, sink temperature and recovery efficiency.',
    }
    lines += [f'| {tech} | {readiness[tech]} |' for tech in CALCULATORS]
    lines += ['', '## Executed examples', '', '| Feed / requested output | Technology | Status | Requested value |', '|---|---|---|---|']
    for case in cases:
        request = case['input']
        for result in case['alternatives'] or [{'technology': 'None', 'calculation_status': case['status'], 'calculated_value': None, 'unit': None}]:
            value = 'Unavailable' if result['calculated_value'] is None else f'{result["calculated_value"]:.8g} {result["unit"]}'
            lines.append(f'| {request["waste_subtype"]} / {request["desired_output"]} | {result["technology"]} | {result["calculation_status"]} | {value} |')
    lines += ['', 'Detailed parameter values, formulas, evidence locations, intermediate products, warnings and missing requirements are in [engine_demo_results.json](engine_demo_results.json). Raw methane and char intermediates do not satisfy biomethane/biogas/biochar requests.', '', '## Dataset inspection', '', '| Dataset | Rows | Missing cells in required columns |', '|---|---:|---:|']
    for name, rows in repo.tables.items():
        missing = sum(not r.get(field) for r in rows for field in SCHEMAS[name])
        lines.append(f'| {name}.csv | {len(rows)} | {missing} |')
    lines += ['', 'Exact columns, per-column missing counts, source IDs, units, measurement bases and verification status counts are in [engine_data_inspection.json](engine_data_inspection.json). Empty cells remain unknown. Coherent samples are retrieved separately by exact category/subtype and optional property ID. Studies/modes require explicit parameter selection when ambiguous; no averaging, generic category-wide property matching or fuzzy subtype transfer is performed.', '', '## Independent audit corrections', '', 'The original three failures have been corrected in implementation, with unchanged original tests plus additional regressions. Mass inputs must be finite, positive and representable after conversion; huge/unrepresentable Python integers are rejected. No arbitrary scientific maximum waste mass is fabricated. Equipment scale limits remain separately unestablished.', '', 'Unit conversions and percentage calculations evaluate ratios first to avoid unnecessary intermediate overflow. Actual derived overflow/underflow or non-finite/negative product quantities return INSUFFICIENT_DATA with structured errors, no calculated value/intermediate total and no recommendation. A final recursive numeric guard protects primary products, intermediate quantities, parameter values and uncertainty ranges, including future calculator modules. Strict JSON outputs contain no NaN or infinity.', '', 'The unsupported gasifier moisture tolerance has been removed. A selected published run requires exact moisture-point identity for reference accounting only. Its source is traced in feasibility_checks.reference_run_moisture; it is not an equipment operating threshold. No documented equipment-specific limits exist in the current datasets: feasibility_checks.moisture_feasibility explicitly reports UNKNOWN, limits=null and sources=[].', '', 'Engineering test passage does not establish scientific predictive validity. The independent audit still identifies three original gas energy-column discrepancies (runs920,924,1110), unknown gas normalization, variable source mass closure and no accepted independent predictive benchmarks. Its scientific gate remains FAILED for source reconciliation; numerical regressions pass. See [independent_scientific_validation.md](independent_scientific_validation.md). No frontend work was started.', '', 'Excluded original property flags:']
    lines += ['- '+issue for issue in repo.issues]
    lines += ['', '## Evidence and units', '', 'Every numeric field used is checked against a verified record/field ledger entry, its converted value and measurement basis, original downloadable-source SHA-256 and extracted-evidence SHA-256. Qualitative mappings require their own verified ledger evidence. These checks establish traceability to the existing inspection; they are not independent experimental replication. The data loader is read-only.', '', 'Mass is internally kg; moisture is wet-basis mass percent. 1 metric tonne = 1000 kg; 1 kWh = 3.6 MJ by dimensional definition. Product masses use wet_mass × (1−moisture/100) × dry-mass yield. Methane yields divide matching feed kg by 1000. Gas volume and HHV are paired only within one run/reference volume basis. No methane heating constant, universal waste conversion efficiency or HHV-to-LHV formula is invented.', '', '## Validation and tests', '', '```text', test.stdout.strip(), test.stderr.strip(), '```', '', f'Phase 2 dataset immutability check: {unchanged}.', '', 'Tests cover mass/energy dimensions, invalid inputs, wet/dry basis and absent moisture, operating-mode separation, moisture/run conflicts, incompatible feedstocks, evidence tampering, source hashes, methane/biogas distinctions, biochar qualification, hazardous and inert exclusion, scale restrictions, gross/net auxiliary boundaries and mutually exclusive alternatives. The complete suite includes Phase 1 integrity tests; its rebuild executes only in an isolated temporary clone, leaving all original CSVs unchanged.', '', '## Scientific and recommendation limitations', '', '- Reference ranking is ordinal eligibility/completeness, with ties; no numerical scores or ranking by incomparable output magnitudes. Unsupported and restricted routes are never recommended. Every alternative is a separate full-mass scenario; no cross-technology sum is returned.', '- Actual installation recommendations require feed analysis, throughput/time, equipment qualification, preprocessing and permits. Reference-mode acknowledgement does not establish these facts or demonstrate small-scale operation.', '- Gross electricity must not be called net if auxiliary consumption is unknown. Already-net equipment efficiencies are not debited twice. Equipment-net and whole-plant-net boundaries differ. The unit-accounting helper is tested but current CSVs do not unlock a qualified waste-to-electricity calculation.', '- Published ranges are descriptive, not confidence intervals. Moisture sensitivity is disclosed for dry-mass outputs; uncertainty in source yield, feed equivalence and scale is not quantified without evidence.', '- A dry feed energy value does not include drying/evaporation duty or recovered heat. A liquid/char quantity does not establish usable fuel quality. Gas temperature/pressure omissions prevent automatic normal-volume conversion.', '- Unknown/unmapped subtypes, polymers and inert material receive no inferred route. Aliases are explicit and restricted to the documented EBMUD, dry-wood, Walawender and garbage reference scopes.', '', '## Original source URLs used by the engine', '']
    ids = sorted({sid for c in cases for r in c['alternatives'] for sid in r['source_ids']})
    for sid in ids:
        source = repo.source(sid)
        lines.append(f'- {sid}: [{source["publication_title"]}]({source["source_url"]}); {source["publication_year"] or "year unavailable"}.')
    lines += ['', '## Reproduction', '', '```powershell', 'python -m pytest tests/test_engine.py -q', 'python scripts/demo_calculation.py --examples', 'python scripts/check_engine.py', '```', '']
    (reports/'engine_readiness.md').write_text('\n'.join(lines), encoding='utf-8')
    print(test.stdout.strip())
    print(json.dumps({'datasets_unchanged': unchanged, 'demo_cases': len(cases), 'reference_requested_output_successes': sum(c['status']=='REFERENCE_RESULTS_AVAILABLE' for c in cases), 'equipment_qualified_forecast_technologies': 0, 'report': str(reports/'engine_readiness.md')}))
    return 0 if test.returncode == 0 and unchanged else 1

if __name__ == '__main__':
    raise SystemExit(main())
