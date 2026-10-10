"""Validate evidence, conversions, schemas, identities, units and physical consistency."""
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from urllib.parse import urlparse
from common import ROOT, SCHEMAS, CATEGORIES, TECHNOLOGIES, read_csv, sha, load_logs, numeric

def property_numeric_columns(columns):
    return [c for c in columns if '_pct' in c or c.endswith('_mj_kg')]

def recompute(original, formula):
    x=float(original)
    if formula=='identity': return x
    if formula=='x / 1000': return x/1000
    if formula=='100 - x': return 100-x
    if formula=='(x - 32) * 5 / 9': return (x-32)*5/9
    m=re.fullmatch(r'x \* 100 / \(100 - ([0-9.]+)\)',formula)
    if m: return x*100/(100-float(m.group(1)))
    raise ValueError('Unsupported conversion formula: '+formula)

def validate():
    errors=[]
    warnings=[]
    tables={}
    columns={}
    def error(message): errors.append(message)
    def warning(message): warnings.append(message)
    for name,required in SCHEMAS.items():
        try: columns[name],tables[name]=read_csv(name)
        except (FileNotFoundError, UnicodeError, csv.Error) as exc:
            error(f'{name}: cannot read CSV: {exc}')
            tables[name]=[]; columns[name]=[]
        missing=set(required)-set(columns[name])
        if missing: error(f'{name}: missing schema columns {sorted(missing)}')
        if len(columns[name])!=len(set(columns[name])): error(f'{name}: repeated column names')
        seen=set()
        for row in tables[name]:
            if None in row or any(v is None for v in row.values()): error(f'{name}: malformed CSV row')
            # Compare content without artificial IDs or status columns.
            excluded=['waste_id','parameter_id','verification_status']+([] if name=='source_verification' else ['record_id'])
            content=tuple((k,v) for k,v in row.items() if k not in excluded)
            if content in seen: error(f'{name}: duplicate content record')
            seen.add(content)
        identity='source_id' if name=='sources' else 'parameter_id' if name=='source_verification' else 'record_id'
        ids=[r.get(identity,'') for r in tables[name] if r.get(identity,'')]
        if len(ids)!=len(set(ids)): error(f'{name}: duplicate {identity}')
    sources={r['source_id']:r for r in tables['sources']}
    logs=load_logs()
    for row in tables['sources']:
        sid=row['source_id']
        if urlparse(row['source_url']).scheme!='https': error(f'{sid}: source URL must be HTTPS')
        if row['publication_year'] and (not row['publication_year'].isdigit() or not 1800<=int(row['publication_year'])<=date.today().year): error(f'{sid}: invalid publication year')
        if row['doi'] and not re.fullmatch(r'10\.\d{4,9}/\S+',row['doi']): error(f'{sid}: malformed DOI')
        try: date.fromisoformat(row['access_date'])
        except ValueError: error(f'{sid}: invalid access date')
        if not row['license']: error(f'{sid}: missing license/access terms')
        if row['dataset_filename']:
            path=ROOT/row['dataset_filename']
            if not path.exists() or sha(path)!=row['sha256']: error(f'{sid}: original source hash mismatch/missing original')
        if row.get('verification_status')=='verified' and row.get('retrieval_status')!='downloaded': error(f'{sid}: verified source not retrieved')
    ledger=defaultdict(list)
    records={name:{r.get('record_id'):r for r in rows} for name,rows in tables.items() if name not in ['sources','source_verification']}
    for v in tables['source_verification']:
        if v['source_id'] not in sources: error('Verification references unknown source '+v['source_id'])
        if v['verification_status']!='verified': continue
        name=v['dataset_name']; rid=v['record_id']; field=v['field_name']
        ledger[(name,rid,field)].append(v)
        row=records.get(name,{}).get(rid)
        if not row: error(f'{name}/{rid}: orphan evidence'); continue
        if row['source_id']!=v['source_id']: error(f'{rid}: mismatched evidence source')
        source=sources.get(v['source_id'],{})
        if source.get('retrieval_status')!='downloaded': error(f'{rid}: evidence source unavailable')
        path=ROOT/v['evidence_file']
        if not path.exists() or sha(path)!=v['evidence_sha256']: error(f'{rid}/{field}: extracted evidence missing or hash mismatch')
        if v['raw_sha256']!=source.get('sha256'): error(f'{rid}/{field}: original-source hash mismatch')
        if not v['evidence_location'] or not v['evidence_text']: error(f'{rid}/{field}: missing evidence text/location')
        if v.get('evidence_image') and not (ROOT/v['evidence_image']).exists(): error(f'{rid}/{field}: missing visual review image')
        if v['evidence_kind']=='qualitative':
            if row.get(field)!=v['converted_value']: error(f'{rid}: qualitative evidence changed')
            continue
        try:
            actual=float(row[field]); original=float(v['original_value'].replace(' ','')); converted=float(v['converted_value'])
            expected=recompute(original,v['conversion_formula'])
            if not all(math.isfinite(x) for x in [actual,original,converted,expected]): error(f'{rid}/{field}: nonfinite number')
            if not math.isclose(actual,converted,rel_tol=1e-8,abs_tol=1e-7): error(f'{rid}/{field}: CSV differs from verification value')
            if not math.isclose(expected,converted,rel_tol=1e-8,abs_tol=1e-7): error(f'{rid}/{field}: invalid conversion')
            if not v['original_unit'] or not v['converted_unit']: error(f'{rid}/{field}: unit missing')
        except (ValueError,KeyError,ZeroDivisionError) as exc: error(f'{rid}/{field}: invalid numeric evidence: {exc}')
    for name in records:
        for row in tables[name]:
            rid=row['record_id']
            if row['source_id'] not in sources: error(f'{rid}: unknown source')
            if row.get('verification_status')=='verified' and not any(k[0]==name and k[1]==rid for k in ledger): error(f'{rid}: verified record has no evidence')
            if row.get('waste_category') and row['waste_category'] not in CATEGORIES: error(f'{rid}: unknown waste category')
            tech=row.get('technology',row.get('technology_name'))
            if tech and tech not in TECHNOLOGIES: error(f'{rid}: unknown technology')
            ncols=property_numeric_columns(columns[name]) if name=='waste_properties' else ['value_min','value_typical','value_max'] if name=='conversion_parameters' else ['capacity','nominal_capacity','electrical_efficiency_pct','thermal_efficiency_pct','operating_temperature_c','auxiliary_energy_consumption'] if name=='technology_performance' else []
            for field in ncols:
                value=row.get(field,'')
                if value=='': continue
                try:
                    val=float(value)
                    if not math.isfinite(val): raise ValueError('nonfinite')
                    if not ledger.get((name,rid,field)): error(f'{rid}/{field}: unsupported numerical value')
                    if '_pct' in field or field.endswith('efficiency_pct'):
                        if not 0<=val<=100: error(f'{rid}/{field}: percentage outside 0-100')
                    elif field=='operating_temperature_c':
                        if not -273.15<val<2500: error(f'{rid}: invalid temperature')
                    elif val<0: error(f'{rid}/{field}: negative physical quantity')
                    if field.endswith('_mj_kg') and val>70: error(f'{rid}/{field}: heating value exceeds supported bound')
                except ValueError: error(f'{rid}/{field}: invalid number {value}')
    for row in tables['waste_properties']:
        rid=row['record_id']
        if not row['heating_value_basis']: error(f'{rid}: heating-value basis absent')
        if row['hhv_mj_kg'] and 'not explicitly stated' in row['heating_value_basis']: warning(f'{rid}: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion')
        if row['lhv_mj_kg'] and row['hhv_mj_kg'] and numeric(row['lhv_mj_kg'])>numeric(row['hhv_mj_kg']): error(f'{rid}: LHV exceeds HHV on same declared basis')
        if row['moisture_pct'] and row['total_solids_pct'] and not math.isclose(numeric(row['moisture_pct'])+numeric(row['total_solids_pct']),100,abs_tol=0.1): error(f'{rid}: moisture + solids not 100%')
        prox=[numeric(row.get(c,'')) for c in ['volatile_matter_pct_dry','fixed_carbon_pct_dry','ash_pct_dry']]
        if all(x is not None for x in prox) and abs(sum(prox)-100)>0.3:
            if row.get('quality_flag') and row.get('model_ready')=='false': warning(f'{rid}: source-published proximate mass closure {sum(prox):.2f}%; quarantined from model-ready data')
            else: error(f'{rid}: proximate dry mass closure {sum(prox)}%')
        if any(row.get(c) for c in ['carbon_pct_dry','hydrogen_pct_dry','oxygen_pct_dry','nitrogen_pct_dry','sulfur_pct_dry']) and not row.get('ultimate_analysis_basis'): error(f'{rid}: elemental analysis basis absent')
        if any(row.get(c) for c in ['volatile_matter_pct_dry','fixed_carbon_pct_dry']) and not row.get('proximate_analysis_basis'): error(f'{rid}: proximate basis absent')
        if row['volatile_solids_pct_ts'] and not row.get('solids_basis'): error(f'{rid}: volatile solids denominator unspecified')
        ultimate=[numeric(row.get(c,'')) for c in ['carbon_pct_dry','hydrogen_pct_dry','oxygen_pct_dry','nitrogen_pct_dry','sulfur_pct_dry']]
        ash_=numeric(row.get('ultimate_ash_pct_dry',row.get('ash_pct_dry','')))
        if all(x is not None for x in ultimate) and ash_ is not None:
            total=sum(ultimate)+ash_+(numeric(row.get('chlorine_pct_dry','')) or 0)
            if abs(total-100)>2:
                if row.get('quality_flag') and row.get('model_ready')=='false': warning(f'{rid}: source-published ultimate mass closure {total:.2f}%; quarantined from model-ready data')
                else: error(f'{rid}: unexplained ultimate mass closure {total:.2f}%')
    units={'m3 CH4/t','L biogas/h','%','% HHV','lb VS/ft3/day','% dry feed mass','MJ/Nm3','% feedstock energy','% theoretical cellulose-to-ethanol yield','% theoretical xylose-to-ethanol yield','degC','MJ/m3','m3 gas/kg dry chips','% dry chip mass','% dry ash-free feed mass','min','MPa'}
    for row in tables['conversion_parameters']:
        rid=row['record_id']
        if not row['unit'] or row['unit'] not in units: error(f'{rid}: undocumented unit {row["unit"]}')
        if not row['measurement_basis'] or not row['operating_conditions']: error(f'{rid}: missing basis or conditions')
        vals=[numeric(row[c]) for c in ['value_min','value_typical','value_max'] if row[c]!='']
        if not vals: error(f'{rid}: numerical parameter has no value')
        if vals!=sorted(vals): error(f'{rid}: inverted min/typical/max')
        if '%' in row['unit'] and any(not 0<=x<=100 for x in vals): error(f'{rid}: yield/efficiency outside 0-100%')
        if row['unit']=='degC' and any(not -273.15<x<2500 for x in vals): error(f'{rid}: temperature outside physical bound')
        if 'Methane production yield'==row['parameter_name'] and 'CH4' not in row['unit']: error(f'{rid}: methane and biogas mixed')
        if 'reference temperature/pressure not stated' in row['measurement_basis']: warning(f'{rid}: gas volume normalization unknown; keep original volume unit')
    for row in tables['technology_performance']:
        rid=row['record_id']
        if row['capacity'] and not row.get('capacity_unit'): error(f'{rid}: missing equipment capacity unit')
        if row['auxiliary_energy_consumption'] and not row.get('auxiliary_energy_unit'): error(f'{rid}: auxiliary unit missing')
        if row['electrical_efficiency_pct'] and not row.get('efficiency_basis'): error(f'{rid}: efficiency HHV/LHV basis absent')
        if row['electrical_efficiency_pct'] and row['thermal_efficiency_pct'] and numeric(row['electrical_efficiency_pct'])+numeric(row['thermal_efficiency_pct'])>100.2: error(f'{rid}: CHP output exceeds fuel input')
    for row in tables['technology_mapping']:
        rid=row['record_id']
        if not ledger.get(('technology_mapping',rid,'mapping_evidence')): error(f'{rid}: unsupported mapping')
        if not row['required_conditions'] or not row['limitations']: error(f'{rid}: missing mapping safeguards')
        if row['feasibility_status'] not in ['conditional','demonstrated','restricted','not_applicable']: error(f'{rid}: unknown feasibility')
        if row['waste_category']=='Hazardous and medical waste' and (row.get('hazard_flag')!='true' or row['feasibility_status']!='restricted' or not row.get('regulatory_restrictions')): error(f'{rid}: unsafe hazardous-waste mapping')
        if row['waste_category']=='Inert waste' and row['feasibility_status']!='not_applicable': error(f'{rid}: inert waste incorrectly assigned fuel conversion')
    summary={name:{'rows':len(rows),'verified_rows':sum(r.get('verification_status')=='verified' for r in rows)} for name,rows in tables.items()}
    result={'passed':not errors,'errors':errors,'warnings':warnings,'counts':summary,
            'input_hashes':{name:sha(ROOT/'data'/f'{name}.csv') for name in SCHEMAS},
            'waste_category_coverage':sorted({r['waste_category'] for name in ['waste_properties','technology_mapping'] for r in tables[name]}),
            'technology_coverage':sorted({r['technology'] for name in ['technology_mapping','conversion_parameters'] for r in tables[name]}|{r['technology_name'] for r in tables['technology_performance']})}
    (ROOT/'reports/validation_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    report=['# Data quality report','',f'Validation: {"PASS" if not errors else "FAIL"}. Errors: {len(errors)}. Warnings: {len(warnings)}.','',
            'Verified means inspected original-source evidence with archived hashes and a traceable field value. It does not mean independently replicated, universally representative, or model-ready.','',
            '| CSV | Rows | Source-verified rows |','|---|---:|---:|']
    report.extend(f'| {name}.csv | {v["rows"]} | {v["verified_rows"]} |' for name,v in summary.items())
    report+=['','Checks: required schemas; numeric types and finiteness; percentage/temperature/heating-value bounds; min/typical/max ordering; duplicates; source IDs; original and extracted file hashes; numerical-field evidence coverage; reproducible conversion formulae; measurement bases; gas identities; equipment capacity/auxiliary units; CHP energy balance; hazardous/inert mapping safeguards.','',
             'Blank values remain missing. Published zeros are accepted only where explicitly present in original evidence. No imputation, artificial yields, or category-average sample construction is performed.','',
             '## Errors','']+[f'- {e}' for e in errors or ['None.']]+['','## Warnings','']+[f'- {w}' for w in warnings or ['None.']]
    (ROOT/'reports/data_quality_report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    if not errors:
        subset_ids={(name,r['record_id']) for name in records for r in tables[name] if r.get('verification_status')=='verified' and r.get('model_ready')!='false'}
        for name,rows in tables.items():
            eligible=[r for r in rows if r.get('verification_status')=='verified' and r.get('model_ready')!='false']
            if name=='source_verification':
                eligible=[r for r in eligible if (r['dataset_name'],r['record_id']) in subset_ids]
            with (ROOT/'data/verified'/f'{name}.csv').open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=columns[name]); writer.writeheader(); writer.writerows(eligible)
    print(json.dumps({'passed':not errors,'errors':errors,'warning_count':len(warnings),'counts':summary},indent=2))
    return result

if __name__=='__main__':
    sys.exit(0 if validate()['passed'] else 1)
