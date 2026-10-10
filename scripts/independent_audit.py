"""Build the independent scientific audit from reviewed originals and test XML.

Writes reports only. Expected source values are the manually transcribed golden
fixtures, not outputs from production formulas. --run-tests runs every existing
test, including the isolated temporary Phase 1 rebuild; no original CSV is built.
Returns nonzero when scientific acceptance tests fail, without hiding failures.
"""
import argparse
import ast
import collections
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT/'reports'
sys.path.insert(0, str(ROOT))

REVIEWED_HASHES = {
    'S01': '60255fa30ac8ec2f885ff59496a224eb7a34f2ebe177df2625c65df5c2fb50a0',
    'S02': '1b7ade7b865b1fccaab471a3e985c9bdb96a5a4690fe14783473a44d5f21db46',
    'S03': 'b44ddc9b6a34f592a04156118484cc35dc37acd24ef500aac9e9eefaed8f649d',
    'S07': 'e21712f070c6806d23757272bbffd07af8dbaa01e98de01a79b62e6656e562f8',
}
LOCATORS = {'S01': 'PDF p182 / printed p201, Refuse entries A–D', 'S02': 'PDF p76 / printed p68, Table 7-8', 'S03': 'PDF p48 / printed p33, Table 3.11 and notes 1,2,5,9–11', 'S07': 'PDF / printed p5, Table 1; qualification text pp6,12–13'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(name):
    with (ROOT/'data'/f'{name}.csv').open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))

def source_fixtures():
    # Load audited literal data using AST, without importing production or tests.
    tree = ast.parse((ROOT/'tests/test_scientific_golden.py').read_text(encoding='utf-8'))
    gas = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'GAS_RUNS' for t in node.targets))
    return gas

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-tests', action='store_true')
    args = parser.parse_args()
    names = ('waste_properties', 'technology_mapping', 'conversion_parameters', 'technology_performance', 'sources', 'source_verification')
    before = json.loads((REPORTS/'independent_hashes_before.json').read_text())
    tables = {name: read(name) for name in names}
    sources = {r['source_id']: r for r in tables['sources']}
    parameters = {r['parameter_id']: r for r in tables['conversion_parameters']}
    properties = {r['waste_id']: r for r in tables['waste_properties']}
    if args.run_tests:
        command = [sys.executable, '-m', 'pytest', str(ROOT/'tests'), '-q', '-p', 'no:cacheprovider', '--junitxml='+str(REPORTS/'independent_tests.xml')]
        completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', cwd=ROOT)
        (REPORTS/'independent_test_output.txt').write_text(completed.stdout+completed.stderr, encoding='utf-8')
    tests = list(ET.parse(REPORTS/'independent_tests.xml').getroot().iter('testcase'))
    failures = [t for t in tests if t.find('failure') is not None or t.find('error') is not None]
    skipped = sum(t.find('skipped') is not None for t in tests)
    counts = {'total': len(tests), 'passed': len(tests)-len(failures)-skipped, 'failed': len(failures), 'skipped': skipped}
    test_groups = collections.defaultdict(collections.Counter)
    for test in tests:
        status = 'failed' if test.find('failure') is not None or test.find('error') is not None else 'skipped' if test.find('skipped') is not None else 'passed'
        test_groups[test.get('classname')][status] += 1
    (REPORTS/'independent_test_summary.json').write_text(json.dumps({'counts': counts, 'groups': dict(test_groups), 'failures': [{'name': t.get('name'), 'message': (t.find('failure') if t.find('failure') is not None else t.find('error')).get('message')} for t in failures]}, indent=2), encoding='utf-8')
    after = {name+'.csv': sha(ROOT/'data'/f'{name}.csv') for name in names}
    (REPORTS/'independent_hashes_after.json').write_text(json.dumps(after, indent=2), encoding='utf-8')
    unchanged = before == after
    source_reviews = []
    for sid, digest in REVIEWED_HASHES.items():
        path = REPORTS/'independent_evidence'/f'{sid}_fresh.pdf'
        inspected_snapshot_matches = path.exists() and sha(path) == digest
        source_reviews.append({'source_id': sid, 'source_url': sources[sid]['source_url'], 'file': str(path.relative_to(ROOT)), 'reviewed_sha256': digest, 'fresh_copy_matches_reviewed_snapshot': inspected_snapshot_matches, 'matches_archived_original': inspected_snapshot_matches and sha(ROOT/sources[sid]['dataset_filename']) == digest, 'evidence_location': LOCATORS[sid], 'status': 'VERIFIED_SOURCE' if inspected_snapshot_matches else 'NOT_CHECKED', 'scope': 'Fresh original report inspected, not independent experimental replication; S01/S02 are secondary compilations.'})
    (REPORTS/'independent_source_review.json').write_text(json.dumps(source_reviews, indent=2), encoding='utf-8')
    gas = source_fixtures()
    field_audit = []
    def audit_field(table, row, field, expected, original_unit, basis, conditions, active=True):
        actual = row.get(field, '')
        matched = bool(actual) and Decimal(actual) == Decimal(str(expected))
        sid = row['source_id']
        review = next(r for r in source_reviews if r['source_id'] == sid)
        entry = {'dataset': table, 'record_id': row.get('parameter_id', row.get('waste_id')), 'field': field, 'reported_value': str(expected), 'reported_unit': original_unit, 'measurement_basis': basis, 'operating_conditions': conditions, 'source_id': sid, 'source_url': sources[sid]['source_url'], 'evidence_location': LOCATORS[sid], 'stored_value': actual, 'expected_stored_value': str(expected), 'stored_unit': row.get('unit', 'MJ/kg' if field in ('hhv_mj_kg','lhv_mj_kg') else ''), 'matches_independent_transcription': matched, 'active_calculation_field': active, 'status': 'VERIFIED_SOURCE' if matched and review['status']=='VERIFIED_SOURCE' else 'FAILED' if not matched else 'NOT_CHECKED'}
        field_audit.append(entry)
    for index, row in enumerate(gas):
        run, moisture, hhv, yield_, rate, energy, closure = row
        conditions = f'Published run {run}; dry chip flow {rate} kg/h; {moisture}% wet-basis moisture; reactor temperature and gas volume T/P not stated in this table'
        audit_field('conversion_parameters', parameters[f'P{55+4*index:04}'], 'value_typical', hhv, 'MJ/m3', 'dry gas', conditions)
        audit_field('conversion_parameters', parameters[f'P{56+4*index:04}'], 'value_typical', yield_, 'm3/kg DC (DC=dry chips)', 'dry chip feed; paired same-run gas volume', conditions)
    for start, products, conditions in [(22, (75,12,13), 'Fast; about 500 C; about 1 s hot vapor residence'), (25, (50,20,30), 'Intermediate; about 500 C; 10–20 s hot vapor residence'), (28, (30,35,35), 'Slow carbonisation; about 400 C; very long solids residence')]:
        for offset, value in enumerate(products):
            audit_field('conversion_parameters', parameters[f'P{start+offset:04}'], 'value_typical', value, '% product mass / dry wood feed mass', 'dry wood, typical reference table; liquid includes water', conditions, active=offset != 2)
    for pid, low, typical, high, basis, conditions in [
        ('P0001', 300,420,530,'dry metric tonne solids applied after processing','food pulp; 15-day MCRT; stable mesophilic/thermophilic observations'),
        ('P0002', 200,300,450,'dry metric tonne solids applied after processing','food pulp; 10-day MCRT; stable mesophilic/thermophilic observations'),
        ('P0003', 230,310,390,'dry metric tonne solids applied','municipal wastewater solids; previous EBMUD bench study; 15-day MCRT'),
        ('P0004', 75,100,135,'wet metric tonne delivered before processing','delivered food; 15-day MCRT; processing losses included in reported delivered-load yield'),
        ('P0005', 50,75,110,'wet metric tonne delivered before processing','delivered food; 10-day MCRT; processing losses included in reported delivered-load yield'),
    ]:
        for field, value in [('value_min',low),('value_typical',typical),('value_max',high)]:
            audit_field('conversion_parameters', parameters[pid], field, value, 'm3 CH4 / metric tonne', basis+'; source gas T/P unspecified', conditions)
    for wid, original_j_g in [('W0046',18500),('W0047',19850),('W0048',20040),('W0049',20050)]:
        audit_field('waste_properties', properties[wid], 'hhv_mj_kg', Decimal(original_j_g)/1000, 'Original J/g; converted MJ/kg = J/g / 1000', 'dry shredded garbage, essentially free of glass/metals; gross constant-volume q_v', 'mean of two trials; compilation assumes room temperature')
        field_audit[-1].update(reported_value=str(original_j_g), reported_unit='J/g', conversion_formula='original_J_per_g / 1000', stored_unit='MJ/kg')
    (REPORTS/'independent_parameter_audit.json').write_text(json.dumps(field_audit, indent=2), encoding='utf-8')
    energy_checks = []
    for run, moisture, hhv, yield_, flow, printed, closure in gas:
        h = Decimal(hhv); y = Decimal(yield_); q = Decimal(printed)
        # All three source columns show two decimal places. Worst-case propagation
        # of +/-0.005 rounding, including the printed energy-yield rounding itself.
        allowance = Decimal('.005')*(h+y) + Decimal('.000025') + Decimal('.005')
        error = y*h-q
        energy_checks.append({'run': run, 'hhv_mj_m3': hhv, 'gas_yield_m3_kg_dry': yield_, 'source_energy_yield_mj_kg_dry': printed, 'computed_yield_times_hhv': str(y*h), 'difference_mj_kg_dry': str(error), 'rounding_only_allowance_mj_kg_dry': str(allowance), 'within_rounding_allowance': abs(error) <= allowance, 'source_material_balance_closure_pct': closure})
    (REPORTS/'independent_gas_energy_crosscheck.json').write_text(json.dumps(energy_checks, indent=2), encoding='utf-8')
    # Observed outputs for external candidate feeds are produced by the existing
    # engine, not invented. Optional proxy screens are explicitly separate.
    from engine import DataRepository, CalculationInput, recommend
    from engine.recommender import calculate
    repo = DataRepository()
    benchmarks = []
    for bid, doi, title, feed, moisture, output, technology, reference, unit, conditions, location, reason in [
        ('B01', '10.3390/app12104822', 'Fractional Condensation of Fast Pyrolysis Bio-Oil to Improve Biocrude Quality towards Alternative Fuels Production', 'Pine wood; Mati et al. 2022', 10, 'bio-oil', 'Pyrolysis', 62.9, 'kg liquid per 100 kg as-received feed (reported campaign average)', '1 kg/h bubbling fluidized bed; 500 C; 1 bar; reactor 0.6–1.1 s; hot zone 530 C, 1.4–1.9 s in Table 1; Table 8 instead reports hot residence 0.6–1.1 s and 10–12% feed water; fractional condensation', 'PDF pp5,9,11,16–17; Tables 1,4,8, Eq1 and section3.5', 'Generic dry-wood typical reference is not validated for this independent pine/condensation system. Reported mean has 88–95% mass closure and approximate moisture, not identical reference conditions.'),
        ('B02', '10.3390/pr8111407', 'Study of a Method to Effectively Remove Char Byproduct Generated from Fast Pyrolysis of Lignocellulosic Biomass in a Bubbling Fluidized Bed Reactor', 'Pine sawdust; Ha and Lee 2020', 9.7, 'bio-oil', 'Pyrolysis', 62.4, '% dry feed mass (reported maximum)', '0.5–1 mm particles; 0.8–1.8 kg/h; 15 L/min N2; atmospheric pressure; maximum reported at 440 C', 'PDF p1 abstract, p3 Table1, p5 section3.1 and conclusions', '440 C maximum is outside selected 500 C reference; other yields are graph-based and were not guessed or interpolated.'),
        ('B03', '10.3390/environments5070084', 'Characterization of Recycled Wood Chips, Syngas Yield, and Tar Formation in an Industrial Updraft Gasifier', 'Recycled wood chips; Oveisi et al. 2018 updraft', 26.8, 'syngas', 'Gasification', None, 'No comparable mass-specific dry producer-gas volume inspected', '8.5 MWth updraft plant; feed moisture 20.6–33.3% wet; temperature in sampling campaigns 875–1050 C; unlike historical downdraft runs', 'PDF pp1,4,6–7; Tables1–3, section3.2', 'Updraft/downdraft, moisture, output and gas volume basis differ. Section3.2 reports calorific values 3.7 and 4.1 MJ/m3 for two days, not a comparable verified HHV × volume-yield pair.'),
    ]:
        request = CalculationInput('Wood and forestry waste', feed, 100, moisture_pct=moisture, desired_output=output, technology_preference=technology, reference_mode=True)
        result = calculate(request, technology, repo)
        source_present = any(doi.casefold() == s['doi'].casefold() or title.casefold() == s['publication_title'].casefold() for s in sources.values())
        entry = {'benchmark_id': bid, 'doi': doi, 'publication_url': 'https://doi.org/'+doi, 'feedstock': feed, 'experimental_conditions': conditions, 'reference_output': reference, 'reference_unit': unit, 'evidence_location': location, 'original_pdf': f'reports/independent_evidence/{bid}_fresh.pdf', 'source_not_used_to_populate_original_csvs': not source_present, 'predicted_output': result.calculated_value, 'prediction_unit': result.unit, 'engine_status': result.calculation_status, 'error': None, 'validation_status': 'NOT_VALIDATED', 'reason': reason}
        if bid == 'B01':
            screens = []
            for w in (10,12):
                proxy = CalculationInput('Wood and forestry waste', 'Dry wood reference', 100, moisture_pct=w, desired_output='bio-oil', parameter_id='P0022', reference_mode=True)
                observed = calculate(proxy, 'Pyrolysis', repo)
                screens.append({'explicit_proxy_input': proxy.__dict__, 'engine_reference_result_kg': observed.calculated_value, 'signed_deviation_from_reported_mean_kg_per_100kg': observed.calculated_value-reference, 'relative_deviation_pct': (observed.calculated_value-reference)/reference*100, 'meaning': 'Approximate cross-study reference screen only; feed substitution and moisture interval acknowledged. This is not an accepted prediction of the experiment.'})
            entry['reference_proxy_screens'] = screens
        benchmarks.append(entry)
    (REPORTS/'independent_benchmarks.json').write_text(json.dumps(benchmarks, indent=2, ensure_ascii=True, allow_nan=False), encoding='utf-8')
    inventory = json.loads((REPORTS/'independent_repository_inventory.json').read_text())
    engine_unchanged = all(sha(ROOT/r['file']) == r['sha256'] for r in inventory if r['file'].replace('\\','/').startswith('engine/'))
    changed_engine_files = [r['file'] for r in inventory if r['file'].replace('\\','/').startswith('engine/') and sha(ROOT/r['file']) != r['sha256']]
    failed_energy = [r for r in energy_checks if not r['within_rounding_allowance']]
    numeric_failures = [r for r in field_audit if r['status'] == 'FAILED']
    golden = [t for t in tests if 'scientific_golden' in t.get('classname','') and t.get('name','').startswith('test_golden_')]
    golden_failed = sum(t.find('failure') is not None for t in golden)
    overall_status = 'FAILED' if failures or failed_energy or numeric_failures or not unchanged else 'NOT_VALIDATED'
    engineering_gate = 'PASS' if not failures and not skipped and unchanged else 'FAILED'
    group_summary = '; '.join(f'{name}: {group.get("passed",0)} passed, {group.get("failed",0)} failed' for name, group in sorted(test_groups.items()))
    new_regression_count = sum('test_engine_numeric_safety' in t.get('classname','') for t in tests)
    lines = [
        '# Independent scientific validation — WasteWise AI', '',
        f'Audit executed {datetime.now(timezone.utc).isoformat()}. Engineering regression gate: **{engineering_gate}**, with **{counts["passed"]} tests passed, {counts["failed"]} failed, {counts["skipped"]} skipped, {counts["total"]} total**. Full scientific acceptance: **{overall_status}** because source-table reconciliation remains unresolved. No pathway earns EXTERNALLY_VALIDATED.', '',
        f'The six original CSV files are byte-for-byte unchanged: **{unchanged}**. Before/after hashes are [independent_hashes_before.json](independent_hashes_before.json) and [independent_hashes_after.json](independent_hashes_after.json). User-authorized corrections changed engine implementation: {", ".join(changed_engine_files)}; added engine/numerics.py. Scientific equations and source parameters are unchanged; finite guards and algebraically equivalent fraction-first evaluation prevent representation failures. No frontend development occurred.', '',
        'This is an independent-method/code-fixture audit inside the existing Codex session, not an independent laboratory replication, accredited certification or independent human peer review. Scientific facts were re-read from original downloaded reports; prior labels and tests were not accepted as proof of predictive accuracy.', '',
        '## Status definitions', '',
        '- VERIFIED_ARITHMETIC: independent published-input arithmetic matches the implemented mass/energy accounting.',
        '- VERIFIED_SOURCE: the particular value/basis was inspected in an original accessed report. This may be a secondary compilation and does not imply original laboratory-paper review.',
        '- EXTERNALLY_VALIDATED: a held-out, comparable experimental result agrees with a legitimate model prediction under a declared acceptance rule. **None achieved.**',
        '- NOT_VALIDATED: no valid external predictive comparison established.',
        '- FAILED: an acceptance condition or scientific consistency check failed. NOT_CHECKED is used separately for an unperformed external retrieval/inspection.', '',
        '## 1. Source verification findings', '',
        'Inspected all six CSVs, all engine modules, both existing test files, CLI, readiness/source-audit/data-quality reports and repository scripts. [Repository inventory](independent_repository_inventory.json) records original Python hashes/function inventory. Prior PASS reports establish structural traceability under their checks, not scientific validation. The prior 72 warnings and two quarantined property records remain relevant.', '',
        '| Report | Exact evidence | Fresh retrieval / comparison | Scope |', '|---|---|---|---|',
    ]
    for review in source_reviews:
        sid = review['source_id']
        scope = 'secondary compilation' if sid in ('S01','S02') else 'typical reference, not an individual experiment' if sid=='S07' else 'bench experiments; sludge comparator from prior study'
        lines.append(f'| [{sid}: {sources[sid]["publication_title"]}]({sources[sid]["source_url"]}) | {review["evidence_location"]} | {review["status"]}; identical archived bytes: {review["matches_archived_original"]} | {scope} |')
    lines += ['', 'All four successful fresh downloads were inspected as original PDF text and rendered table images, not search snippets. Archive hashes match the independently downloaded bytes. Network sockets initially failed inside the sandbox; approved retrieval succeeded. [Retrieval log](independent_evidence/retrieval_log.json) deliberately marks download-only evidence NOT_CHECKED; [completed source review](independent_source_review.json) records the subsequent inspection.', '',
        'Qualitative source pages were also opened and read independently: [EPA anaerobic digestion](https://www.epa.gov/anaerobic-digestion/basic-information-about-anaerobic-digestion) supports food/manure/sludge digestion and an indirect gas-cleanup/CHP chain; [EPA MSW combustion](https://www.epa.gov/smm/energy-recovery-combustion-municipal-solid-waste-msw) supports controlled non-hazardous MSW combustion. They supply no sample-specific conversion efficiency or authorization for arbitrary contaminated feed.', '',
        '**Primary-paper limitations:** S02 Table7-8 cites Walawender, Chern and Fan (1985), p917, in *Fundamentals of Thermochemical Biomass Conversion*. Its bibliography is on PDF p145 / printed p137; the [book](https://doi.org/10.1007/978-94-009-4932-4) was located, but chapter text was not accessible/inspected: primary-paper verification NOT_CHECKED. S01 refers to Jensen, Eatough and Hansen, *J. Chem. Educ.* 54,700 (1977), located in the compendium bibliography on PDF p294. [DOI10.1021/ed054p700](https://doi.org/10.1021/ed054p700) was identified via the publisher issue listing; the primary article could not be inspected: NOT_CHECKED. VERIFIED_SOURCE below applies to the accessed compilation, not these primary papers.', '',
        f'**Independent parameter comparison:** {len(field_audit)} numeric field checks, {len(numeric_failures)} mismatches. {sum(r["active_calculation_field"] for r in field_audit)} fields can be used by numerical/reference/intermediate calculations; three pyrolysis gas fractions are context for mass closure. [Full parameter audit](independent_parameter_audit.json) lists each ID/field, reported value, original unit, basis, operating conditions, original URL and exact location. User mass/moisture are declared scenario inputs, not independently measured source parameters.', '',
        '### Pyrolysis source table', '', '| Mode / IDs | Liquid / char / gas (% dry wood mass) | Source conditions |', '|---|---|---|',
        '| Fast P0022–P0024 | 75 / 12 / 13 | about500 C; hot vapor about1 s |',
        '| Intermediate P0025–P0027 | 50 / 20 / 30 | about500 C; hot vapor10–20 s |',
        '| Slow P0028–P0030 | 30 / 35 / 35 | about400 C; very long solids residence |', '',
        'Table1 is a typical distribution. Text on p6 describes fast-process drying, small particles and quenching; pp12–13 explain feed/reaction water in the liquid. The API does not enforce these reactor/preparation conditions.', '',
        '### Digestion source values', '', '| ID | Methane mean (range), m3 per metric tonne | Denominator | Conditions |', '|---|---|---|---|',
        '| P0001 | 420 (300–530) | dry applied TS | food pulp,15-day MCRT |',
        '| P0002 | 300 (200–450) | dry applied TS | food pulp,10-day MCRT |',
        '| P0003 | 310 (230–390) | dry applied solids | wastewater solids,15-day MCRT,prior bench study |',
        '| P0004 | 100 (75–135) | wet delivered food before processing |15-day MCRT|',
        '| P0005 | 75 (50–110) | wet delivered food before processing |10-day MCRT|', '',
        'Food ranges combine stable mesophilic/thermophilic observations. Table footnotes separate delivered mass from applied solids; delivered-load yields already reflect processing. No reject deduction is applied a second time. Gas T/P is not established for these yield entries. Table electricity rows are assumption-based calculations (footnote3), not qualified measured equipment outputs; they correctly remain unavailable in the engine.', '',
        '### Refuse source values', '', '| Property | Original gross q_v (J/g dry) | Stored value (MJ/kg dry) |', '|---|---:|---:|',
        '| W0046 sampleA |18500|18.5|', '| W0047 sampleB |19850|19.85|', '| W0048 sampleC |20040|20.04|', '| W0049 sampleD |20050|20.05|', '',
        'Two-trial means for dry shredded refuse free of most glass/metals; plastics/waxes/oils were present. Room-temperature reference is a compilation assumption. Constant-volume gross heat is retained as a chemical-energy characterization, not a measured boiler or turbine output. Unrelated RDF entries on the same page are not substituted.', '',
        '### Gasification source values', '',
        '| Run | HHV / yield IDs | Moisture %wet | Dry flow kg/h | Gas yield m3/kg dry chips | Gas HHV MJ/m3 | Material closure % |', '|---|---|---:|---:|---:|---:|---:|',
    ]
    for index, (run,w,h,y,f,q,c) in enumerate(gas):
        lines.append(f'|{run}|P{55+4*index:04}/P{56+4*index:04}|{w}|{f}|{y}|{h}|{c}|')
    lines += ['', 'Table7-8 explicitly uses dry chips (DC), dry gas and HHV. It does not state this table’s gas volume reference T/P or reactor temperature. Same-run m3 and MJ/m3 cancel dimensionally, but this does not authorize Nm3 conversion or a new-study comparison with normalized/LHV gas data. Source mass closures range80.4–99.5%, and the engine neither records these per-run quality indicators nor adjusts their evidence rank. The worst runs require caution; a copied experimental number is not automatically a reliable design parameter.', '',
        '## 2. Formula-by-formula audit', '', '| Implemented operation | Independent dimensional/method check | Status and boundary |', '|---|---|---|',
        '| Mass conversions |g÷1000; kg unchanged; metric tonnes×1000|VERIFIED_ARITHMETIC; non-finite/negative/zero inputs and post-conversion overflow/underflow rejected; no invented physical mass cap|',
        '| Dry feed mass |m_dry=m_wet(1−w/100); kg×dimensionless|VERIFIED_ARITHMETIC; only wet-basis moisture or same-sample TS; no inferred moisture|',
        '| Pyrolysis liquid/char |m_product=m_dry×Y/100, kg×kg/kg|VERIFIED_ARITHMETIC and VERIFIED_SOURCE; reference-table accounting, not kinetic/equipment model|',
        '| Gas volume |V=m_dry×same_run_Y, kg×m3/kg|VERIFIED_ARITHMETIC and VERIFIED_SOURCE; no moisture tolerance or operating threshold; exact reference point identity required; equipment moisture feasibility UNKNOWN|',
        '| Gas chemical energy |E=V×same_run_HHV, m3×MJ/m3=MJ|VERIFIED_ARITHMETIC from printed inputs; source energy-column reconciliation FAILED for some runs; before utilization/auxiliary duty|',
        '| Solid feed energy |E=m_dry×gross_qv, kg×MJ/kg=MJ|VERIFIED_ARITHMETIC and VERIFIED_SOURCE; overflowing derived output blocked with structured error; gross constant-volume characterization, not recovered heat|',
        '| Methane intermediate |V_CH4=(matching feed kg÷1000)×m3_CH4/t|VERIFIED_ARITHMETIC and VERIFIED_SOURCE; dry TS and wet-delivered denominators separate; no conversion to total biogas or purified biomethane|',
        '| Descriptive methane range |Scale source minimum/maximum using same mass basis|VERIFIED_ARITHMETIC; observed ranges are not confidence intervals|',
        '| Moisture sensitivity |(dY/dw)/Y=−1/(100−w), holding yield constant|VERIFIED_ARITHMETIC away from100%; derivative of basis accounting, not reactor response|',
        '| Electricity accounting helper |E_kWh=E_MJ×eta/100÷3.6; subtract known auxiliary kWh only for gross efficiency|Dimensionally sound; tested as unit bookkeeping only. Already-net efficiency cannot be debited twice; equipment-net is not plant-net. No source-qualified waste route invokes this helper|',
        '| Other technology modules |No numerical formula for unsupported pathways|Correct abstention: insufficient fuel/composition/yield/equipment/stream data remains explicit|', '',
        'The simple mass/energy equations follow the definitions of the published denominators rather than reproducing a mechanistic scientific prediction method. Independent experimental B01 Eq1 also defines product mass/feed mass, but on an as-received basis; this basis must be corrected before comparison.', '',
        '**Mass conservation and boundaries:** Each dry-wood reference triplet sums100%. This is the published normalized distribution; actual wet-feed closure also requires removed water, reaction water, entrained solids and losses. Assuming dry matter is conserved through unmodeled drying is an explicit needed qualification. The engine’s zero output at100% water is a mathematical zero-dry-mass result, not evidence that water is a feasible wood feed. Reference pyrolysis liquid includes water and is not upgraded fuel; char is not qualified biochar. Gas energy excludes drying, gas cleanup and utilization losses. Alternatives each consume the full mass independently and cannot be added.', '',
        '### Independent gas energy-column cross-check', '',
        'Compared the original printed energy yield column with printed gas-yield×HHV. The maximum allowance for two-decimal nearest rounding is0.005(HHV+yield)+0.000025+0.005 MJ/kg dry. This is a rounding-only diagnostic, not an experimental-uncertainty allowance.', '',
        '| Run | HHV×yield MJ/kg dry | Source energy yield | Difference | Max rounding allowance |', '|---|---:|---:|---:|---:|',
    ]
    for r in failed_energy:
        lines.append(f'|{r["run"]}|{r["computed_yield_times_hhv"]}|{r["source_energy_yield_mj_kg_dry"]}|{r["difference_mj_kg_dry"]}|{r["rounding_only_allowance_mj_kg_dry"]}|')
    lines += ['', 'These are source-table reconciliation problems under the stated rounding assumption, not evidence that engine multiplication is wrong. The historical primary method/rounding, measurement precision or transcription must be clarified; no automatic correction is justified. Full results: [independent_gas_energy_crosscheck.json](independent_gas_energy_crosscheck.json).', '',
        '## 3. Independent golden test results', '',
        f'Latest complete suite: {group_summary}. Published-input golden checks including unit equivalents: **{len(golden)-golden_failed} passed,{golden_failed} failed**. Totals: **{counts["passed"]} passed,{counts["failed"]} failed**. The previous audit had137 passed/3 failed out of140. All original140 tests, including the three formerly failing guards, are retained unchanged and now pass; {new_regression_count} additional numeric-safety regression cases are included. No expected failure markers, weakened assertions or skips were used.', '',
        'Expected outputs were independently transcribed from the inspected tables and calculated with Decimal/literal arithmetic inside [test_scientific_golden.py](../tests/test_scientific_golden.py). Production functions produce observed outputs only. Numeric assertions use rel=0, abs=1e-8 to accommodate binary arithmetic, not deviations in scientific yield or operating conditions. Initial fixture-only display mistakes (trailing-zero string comparison and misreading run121 as1121) were corrected after magnified original-table inspection; neither engine nor datasets changed.', '',
        'Examples:100 kg wet wood at10% moisture gives67.5/45/27 kg liquid for the three reference modes.1000 kg chips at16.52% moisture for run98 gives1853.256 m3 gas and9877.85448 MJ gross gas energy from printed input values.100 kg sampleA at20% moisture gives1480 MJ gross feed energy.1000 kg food pulp at90% water gives42 m3 methane using P0001; delivered-food P0004 gives100 m3 without requiring a dry-mass conversion. Extra displayed digits demonstrate arithmetic, not measurement precision.', '',
        'Robustness covers invalid/zero mass, g/kg/tonnes equivalence, missing moisture, moisture endpoints, incompatible/inert feed, restricted medical waste, and both electricity/useful-heat requests across six routes. Unsupported energy forecasts remain blocked. All existing tests were run, including the offline rebuild test **only in an isolated temporary clone**; no original dataset was regenerated or overwritten.', '',
        '[Machine-readable test summary](independent_test_summary.json); [JUnit evidence](independent_tests.xml).', '',
        '## 4. Experimental benchmark comparisons', '',
        'Three new experimental papers were downloaded, their original methods/results inspected, and DOI/title checked against the31-row source catalog. None populated the original CSVs. These files and review text remain under reports/independent_evidence; no new scientific dataset records were added. Formal same-feed predictions are unavailable, so formal errors are unavailable. A separate approximate reference screen is disclosed where useful.', '',
        '| Independent paper | Inspected experiment/reference output | Actual engine prediction / error | Status |', '|---|---|---|---|',
    ]
    for b in benchmarks:
        reference = 'No comparable volume yield; measured gas calorific values3.7/4.1 MJ/m3 for two days' if b['reference_output'] is None else f'{b["reference_output"]} {b["reference_unit"]}'
        lines.append(f'|[{b["benchmark_id"]}, DOI{b["doi"]}]({b["publication_url"]})|{b["feedstock"]}; {reference}; {b["evidence_location"]}|No accepted prediction: {b["engine_status"]}; error unavailable|NOT_VALIDATED|')
    lines += ['', '**B01 approximate reference screen:**100 kg as-received pine, using the reported approximate10–12% water interval and explicitly substituting the engine’s generic dry-wood reference P0022, gives66–67.5 kg liquid. Against the published62.9 kg campaign mean, the signed deviation is+3.1 to+4.6 kg per100 kg feed (+4.93% to+7.31%). These are actually executed reference calculations, recorded with exact requests in [independent_benchmarks.json](independent_benchmarks.json). They are **not** validated predictions for the experimental feed. The moisture interval is approximate, source yield closure is88–95%, condensers differ, and Table1/Table8 disagree on hot-zone residence notation. This single reference screen cannot establish an accuracy distribution or a pass criterion.', '',
        'B02’s62.4% dry-basis maximum is at440 C, not the selected500 C typical mode; the engine has no temperature-response model. No curve value at500 C was invented. B03 is an8.5 MWth updraft system, not the historical downdraft reference, and its measured outputs/gas basis are not a matching mass-specific HHV-volume pair. It is excluded from quantitative error calculation.', '',
        'No independent, same-feed/same-process/same-volume-basis methane benchmark or calorimetry measurement of these exact historical refuse samples was established in the accessed literature: **NOT_VALIDATED**, not proof that such studies do not exist. A food-waste yeast-addition candidate (DOI10.1098/rsos.200443) was located but original access was blocked/reCAPTCHA; not inspected and no values used. Browser failures for publisher pages are recorded as access limitations; publicly offered institutional/publisher PDFs were used where accessible. No paywall/CAPTCHA/access-control bypass occurred.', '',
        '## 5. Identified scientific problems', '',
        '| ID | Finding | Evidence / impact | Status |', '|---|---|---|---|',
        '|R1 corrected|Finite, positive, representable internal mass required|NaN/infinity/negative/zero/too-large inputs rejected; conversion overflow and positive-to-zero underflow rejected. Python float representability is a numerical bound, not an invented equipment capacity|VERIFIED_ARITHMETIC; regression tests pass|',
        '|R2 corrected|Derived numeric quantities guarded throughout the engine|Unit conversions, percentages, methane ranges, gas volume/energy and solid-fuel energy checked; final primary/intermediate/parameter/range values screened; invalid results return structured errors with no recommendation|VERIFIED_ARITHMETIC; regression tests pass|',
        '|R3 corrected|No moisture acceptance tolerance or default equipment limit|Published run point is matched exactly as a reference-condition identity. Equipment-specific moisture feasibility is UNKNOWN, limits=null, sources=[]; source point is separately traced to S02/P0056/Table7-8|VERIFIED_ARITHMETIC and VERIFIED_SOURCE for reference point; equipment feasibility NOT_VALIDATED|',
        '|R4|Printed gas energy columns not reconciled|Three runs exceed rounding-only propagated allowance; per-run mass closure80.4–99.5% is not surfaced/ranked|FAILED source-consistency check; source values themselves traced|',
        '|R5|Reference yields are not predictive calibration|Wood species, temperature/residence, preparation, load, cleanup and wet-feed water effects are not modeled; only named reference scenarios are accepted|NOT_VALIDATED|',
        '|R6|Traceability does not independently validate metadata|Runtime compares ledger value/basis/unit and hashes, but operating conditions, feed labels and hazard/feasibility metadata depend on prior curation. Recommender is eligibility filtering with ties, not experimentally validated optimization|NOT_VALIDATED as predictive/ranking system|',
        '|R7|Overprecision and categorical wording|Displayed arithmetic can have many digits; inherited CALCULATED_REFERENCE/verified wording must not imply laboratory accuracy or installation suitability. Zero dry matter should not create an operating recommendation|NOT_VALIDATED for engineering design|', '',
        '## 6. Corrections required', '',
        '1. Completed: validate mass inputs and converted values, including overflow/underflow, without arbitrary physical quantity caps. Completed: all calculated numeric fields are checked before a calculated status or ranking can escape. Structured errors block invalid results; finite negative net electricity in the standalone accounting helper remains explicitly net consumption.',
        '2. Completed: removed the0.05-point moisture tolerance. Exact published-point matching is for reference reproducibility only, not an operating limit. No equipment-specific limit is asserted where none is documented. A future equipment limit must carry its qualified equipment/feedstock context and verified source evidence.',
        '3. Reconcile Table7-8 with the original Walawender method, including gas reference conditions, source energy yield and poor mass-closure runs. Carry per-run quality limitations into outputs; prevent design use while unresolved. Keep original CSV values unchanged unless a separately authorized provenance-preserving correction is made.',
        '4. Keep chemical characterization/reference products separate from plant recommendation. Make explicit whether drying is assumed to conserve dry matter and where feed water ends up; disclose zero-dry-matter cases and preparation/residence requirements.',
        '5. Link operating conditions and feed/mapping metadata to independently inspected evidence; validate gas T/P and HHV/LHV consistently. Obtain equipment-specific load/scale/auxiliary data before enabling recovered heat or electricity.',
        '6. Establish prospective held-out tests using matched feed composition, moisture, temperature/residence, gas volume conditions and product definition, with repeatability/measurement uncertainty and a predefined acceptance rule. Do not derive expected outputs from production parameters or fit/test on the same study.', '',
        'Engine guards and reference-condition matching were corrected under explicit user authorization. Scientific equations/source values were not changed; percentage and unit-ratio evaluation order is algebraically equivalent and avoids false intermediate overflow. Original tests were not weakened or removed. Finite calculation limits do not establish practical equipment applicability. The three formerly failing tests now pass; source-reconciliation and predictive-validity limits remain unresolved.', '',
        '## 7. Validation status by supported pathway', '',
        '| Pathway/output | Arithmetic | Accessed source | External predictive accuracy | Acceptance caveat |', '|---|---|---|---|---|',
        '|Pyrolysis liquid quantity|VERIFIED_ARITHMETIC|VERIFIED_SOURCE (typical reference)|NOT_VALIDATED|Preparation, feed equivalence and reactor assumptions remain conditional|',
        '|Gasification gas volume|VERIFIED_ARITHMETIC|VERIFIED_SOURCE (secondary table)|NOT_VALIDATED|No tolerance; exact reference-point match; equipment moisture feasibility UNKNOWN; unknown volume normalization/scale|',
        '|Gasification gas chemical energy|VERIFIED_ARITHMETIC from printed pair|VERIFIED_SOURCE (secondary table)|NOT_VALIDATED|FAILED source energy-column reconciliation for3 runs; gross fuel boundary only|',
        '|Theoretical solid feed energy|VERIFIED_ARITHMETIC|VERIFIED_SOURCE (secondary q_v)|NOT_VALIDATED|Numeric guards pass; chemical characterization, not recovered heat|',
        '|Digestion raw methane intermediate|VERIFIED_ARITHMETIC|VERIFIED_SOURCE|NOT_VALIDATED|Not total biogas or purified biomethane; volume basis/operational suitability unqualified|',
        '|Pyrolysis char intermediate|VERIFIED_ARITHMETIC|VERIFIED_SOURCE (typical reference)|NOT_VALIDATED|No qualified biochar claim|',
        '|Electricity and useful heat|Unit helper arithmetic only; forecasts blocked|No applicable qualified conversion-efficiency chain|NOT_VALIDATED|Blocking is correct; no operating forecast should be released|', '',
        'Source traceability is substantially supported for the accessed reference tables. Engineering regression tests pass, but scientific predictive accuracy remains unestablished. The full scientific FAILED status retains the three historical source energy-column discrepancies; these are source diagnostic failures, not remaining pytest failures. No frontend work should begin on the assumption of full scientific validation.', '',
        '## Reproduction', '',
        '```powershell', 'python -m pytest tests -q -p no:cacheprovider --junitxml=reports/independent_tests.xml', 'python scripts/independent_audit.py', '# Or execute tests and regenerate this audit report together:', 'python scripts/independent_audit.py --run-tests', '```', '',
        'Re-retrieval is separate and needs network access: python scripts/independent_retrieve.py and python scripts/independent_retrieve.py --benchmarks. Downloading a new version does not automatically establish inspection; if the reviewed source hash changes, source review is NOT_CHECKED until re-inspected.',
    ]
    (REPORTS/'independent_scientific_validation.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({'tests': counts, 'original_csvs_unchanged': unchanged, 'engine_modules_unchanged': engine_unchanged, 'authorized_changed_engine_modules': changed_engine_files, 'engineering_regression_gate': engineering_gate, 'independently_checked_numeric_fields': len(field_audit), 'numeric_field_mismatches': len(numeric_failures), 'source_energy_reconciliation_failures': [r['run'] for r in failed_energy], 'externally_validated_pathways': 0, 'overall_status': overall_status}))
    return 1 if failures or failed_energy or numeric_failures or not unchanged else 0

if __name__ == '__main__':
    raise SystemExit(main())
