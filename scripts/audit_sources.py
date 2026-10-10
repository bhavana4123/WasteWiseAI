"""Audit evidence completeness, source access limitations and uncovered requirements."""
import json
import sys
from collections import Counter, defaultdict
from common import ROOT, SCHEMAS, CATEGORIES, TECHNOLOGIES, read_csv, load_logs, sha

def audit():
    tables={name:read_csv(name)[1] for name in SCHEMAS}
    logs=load_logs()
    verified=[v for v in tables['source_verification'] if v['verification_status']=='verified']
    covered={(v['dataset_name'],v['record_id']) for v in verified}
    unsupported=[]
    for name in ['waste_properties','technology_mapping','conversion_parameters','technology_performance']:
        for row in tables[name]:
            if (name,row['record_id']) not in covered:
                unsupported.append(f'{name}/{row["record_id"]}: no inspected source evidence')
            if row['source_id'] not in logs or logs[row['source_id']]['retrieval_status']!='downloaded':
                unsupported.append(f'{name}/{row["record_id"]}: original source unavailable')
    validation=json.loads((ROOT/'reports/validation_results.json').read_text(encoding='utf-8'))
    if validation.get('input_hashes') and any(sha(ROOT/'data'/f'{name}.csv')!=value for name,value in validation['input_hashes'].items()):
        unsupported.append('CSV changed after validation; rerun validate_datasets.py')
    for err in validation['errors']: unsupported.append('Validation: '+err)
    counts={name:{'rows':len(rows),'verified_rows':sum(r.get('verification_status')=='verified' for r in rows)} for name,rows in tables.items()}
    unused=[s for s in tables['sources'] if s['verification_status']!='verified']
    failed=[s for s in logs.values() if s['retrieval_status']!='downloaded']
    flags=[r for r in tables['waste_properties'] if r.get('model_ready')=='false']
    collection=['# Data collection report','',
        'Scope: source-backed reference and experimental records for WasteWise AI. No training, frontend, cloud deployment, synthetic measurements or unrestricted waste-to-technology Cartesian products were created.','',
        f'Source retrievals: {len(logs)} attempted, {len(logs)-len(failed)} successfully downloaded/parsed, {len(failed)} failed or restricted.',
        f'Scientific/qualitative/equipment records: {sum(len(tables[n]) for n in ["waste_properties","technology_mapping","conversion_parameters","technology_performance"])}. Verification ledger entries and source-catalog rows are separate and must not be counted as new experiments.','',
        '| CSV | Exact rows | Source-verified rows |','|---|---:|---:|']
    collection += [f'| data/{n}.csv | {v["rows"]} | {v["verified_rows"]} |' for n,v in counts.items()]
    collection += ['','Verification requires an inspected original downloaded into data/raw, field-level evidence, a recorded basis/unit and a reproducible formula where transformed. Historical compiled records, manufacturer equipment references, contemporary experiments and qualitative applicability are explicitly distinguished. Verification is provenance verification, not independent replication.','',
        '## Original source URLs and retrieval outcomes','',
        '| ID | Original URL | Status | Bytes | SHA-256 |','|---|---|---|---:|---|']
    for source in tables['sources']:
        log=logs.get(source['source_id'],{})
        collection.append(f'| {source["source_id"]} | [{source["publication_title"]}]({source["source_url"]}) | {log.get("retrieval_status","not_attempted")} | {log.get("bytes","")} | {log.get("sha256","")} |')
    collection += ['','## Download failures and access limitations','']
    collection += [f'- {s["source_id"]}: {s["source_url"]} — {s.get("error","not retrieved")}. Final URL: {s.get("final_url","")}.' for s in failed] or ['- None.']
    collection += ['',
        'Phyllis XLSX links redirect to a login page. The returned HTML is archived as a failure response, not a valid spreadsheet; downloads were not authenticated or bypassed. Public HTML sample views are independently attempted through their normal public URLs.','',
        'Publisher HTML access returning 403 was not bypassed. The open polymer paper was retrieved independently from the official laboratory repository, with DOI 10.1039/d4gc00659c and its CC BY-NC 3.0 terms preserved.','',
        'MNRE and data.gov.in discovery pages are saved but are not treated as numerical conversion measurements. Monetary subsidies and aggregate installed capacities are not conversion yields.','',
        '## Scientific limitations','',
        '- Gross constant-volume q_v and net constant-volume q_v from the NBS/SERI compilation are distinguished. Conventional LHV remains blank unless explicitly identified by the source.',
        '- Dry, dry ash-free, as-received, wet feed and gas-volume bases are preserved. Gas volumes with unknown reference temperature/pressure are not renamed normal cubic metres.',
        '- Pure commercial polymer references do not represent post-consumer contaminated waste.',
        '- Natural-gas CHP equipment efficiencies are not direct waste-to-electricity conversion efficiencies, nor assumed biogas efficiencies.',
        '- PNNL HTL experimental results are separated from modeled goal-case assumptions; calculated HHV is not relabeled an experimental measurement.',
        '- Published standard deviations are not promoted to observed minimum/maximum bounds.',
        '- US regulatory references document restrictions; they do not establish Indian permit eligibility. Local competent-authority review remains required.',
        f'- {len(flags)} source-published composition discrepancies are retained and flagged in the main CSV and excluded from data/verified/waste_properties.csv.']
    (ROOT/'reports/data_collection_report.md').write_text('\n'.join(collection)+'\n',encoding='utf-8')
    audit_report=['# Source audit','',f'Audit: {"PASS" if not unsupported else "FAIL"}. Unsupported records/mappings: {len(unsupported)}.','',
        f'Verified field/qualitative evidence entries: {len(verified)}. Unverified catalog/access entries: {len(tables["source_verification"])-len(verified)}. These are not independent experiments.','',
        '## Evidence checks','',
        'Every populated numerical property, conversion or equipment field must link to an original source and evidence. Validator checks hashes and recalculates unit/basis transformations. Qualitative mappings carry explicit evidence anchors and restrictions. All four scientific CSVs are audited for record-level evidence coverage.','',
        '## Unsupported evidence','']+[f'- {e}' for e in unsupported or ['None detected in the curated records.']]
    audit_report += ['','## Sources not used as verified record evidence','']+[f'- {s["source_id"]}: {s["publication_title"]}; {s["retrieval_status"]}.' for s in unused]
    audit_report += ['','## Source-published quality flags','']+[f'- {r["record_id"]}: {r["waste_subtype"]}: {r["quality_flag"]}. {r["limitations"]}' for r in flags]
    audit_report += ['','## Review limits','',
        'Review performed by Codex using original archived text and rendered table images where layout or OCR required visual inspection. No independent human review, laboratory replication, guarantee of population representativeness or confirmation of all historical primary references is claimed. Secondary compilations are explicitly identified; publication links to those compilations are the provenance, not invented primary-paper DOIs.','',
        'Two cohort reference records can share one numerical measurement value without being duplicates. Verification-ledger uniqueness is by record and field, not by numerical value alone.','',
        'Copyright/access terms are stored per source. Public access is not an unrestricted redistribution license. The polymer article is noncommercial licensed; Phyllis records retain TNO attribution.']
    (ROOT/'reports/source_audit.md').write_text('\n'.join(audit_report)+'\n',encoding='utf-8')
    prop_counts=Counter(r['waste_category'] for r in tables['waste_properties'])
    map_counts=Counter(r['waste_category'] for r in tables['technology_mapping'])
    gaps=['# Missing parameters and coverage','',
        'Missing scientific values are empty CSV cells. No missing quantity has been replaced with zero. Presence of a qualitative mapping does not imply a numerical yield is available.','',
        '## Waste category coverage','',
        '| Requested category | Property records | Mapping records |','|---|---:|---:|']
    gaps += [f'| {cat} | {prop_counts[cat]} | {map_counts[cat]} |' for cat in CATEGORIES]
    conversion_counts=Counter(r['technology'] for r in tables['conversion_parameters'])
    performance_counts=Counter(r['technology_name'] for r in tables['technology_performance'])
    mapping_counts=Counter(r['technology'] for r in tables['technology_mapping'])
    gaps += ['','## Technology coverage','',
        '| Requested technology | Conversion parameter rows | Equipment rows | Mapping rows |','|---|---:|---:|---:|']
    gaps += [f'| {tech} | {conversion_counts[tech]} | {performance_counts[tech]} | {mapping_counts[tech]} |' for tech in TECHNOLOGIES]
    gaps += ['','## Remaining scientific gaps','',
        '- Representative waste-property samples and conversion experiments remain sparse across categories; historical references and pure polymer materials cannot replace local feed characterization.',
        '- Polymer-specific waste pyrolysis/gasification yields and preprocessing evidence for PE, PP, PS, PVC, PET and textile blends are incomplete. PVC and other halogen-containing plastics require dedicated contamination/emissions assessment; no ordinary organic conversion route is assigned.',
        '- Direct measured waste-combustion electrical/thermal efficiencies, RDF/SRF preprocessing energy and fuel specification parameters, and equipment-specific pyrolysis/gasification/HTL energy balances remain incomplete.',
        '- The reported acid-esterification >99% threshold concerns pure fatty acid streams; measured biodiesel yield for actual used cooking oil remains a gap.',
        '- Animal manure digestion yields, feedstock-specific industrial organic waste yields and waste heat recovery device efficiency at specified source/sink temperatures require additional original experiments.',
        '- Landfill gas recovery is qualitatively documented; actual site-specific gas generation/capture rates and auxiliary power are not inferred.',
        '- Gas volume normalization conditions and several gross-heating-value sample moisture bases remain unspecified. They cannot support automatic basis conversions.',
        '- Inert glass, metals and concrete are not assigned calorific values or energy-producing fuel routes; any recovery of sensible heat from hot inert materials belongs to industrial waste heat recovery.',
        '- Hazardous/medical waste is restricted to specialist treatment evidence with blank energy outputs; no untreated material is mapped to ordinary digesters or MSW processes.',
        '- Regulatory permission in India is not established by EPA sources or an MNRE programme page; jurisdiction-specific authorization remains outside these reference datasets.',
        '- Independent review of historical primary papers and resolution of the two published mass-closure discrepancies remain outstanding.']
    gaps += ['','## Missing required-column values','', '| CSV | Column | Blank count |','|---|---|---:|']
    for name in ['waste_properties','conversion_parameters','technology_performance']:
        for col in SCHEMAS[name]:
            count=sum(r.get(col,'')=='' for r in tables[name])
            if count: gaps.append(f'| {name}.csv | {col} | {count} |')
    issues=json.loads((ROOT/'data/processed/build_issues.json').read_text(encoding='utf-8'))
    gaps += ['','## Curated selections not built','']+[f'- {i["selection"]}: {i["reason"]}' for i in issues or [{'selection':'None','reason':'all selected evidence built successfully'}]]
    (ROOT/'reports/missing_parameters.md').write_text('\n'.join(gaps)+'\n',encoding='utf-8')
    result={'passed':not unsupported,'unsupported':unsupported,'source_failures':len(failed),'counts':counts,'property_quality_flags':len(flags),'coverage':{'property_categories':dict(prop_counts),'mapping_categories':dict(map_counts),'technology_parameter_counts':dict(conversion_counts)}}
    (ROOT/'reports/audit_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__': sys.exit(0 if audit()['passed'] else 1)
