"""Build six CSVs from inspected originals. Curated table selections are not synthetic data.

Every numerical field has an evidence entry. Unknown bases remain explicit; missing
scientific values stay empty. The builder checks archived originals and text anchors.
"""
import json
import re
from collections import defaultdict
from common import ROOT, SCHEMAS, write_csv, load_logs, evidence_file, norm, sha

DATA = defaultdict(list)
VERIFICATION = []
ISSUES = []
LOGS = {}

def proof(source, page, anchor='', end=None, scope=False):
    log = LOGS.get(source, {})
    if log.get('retrieval_status') != 'downloaded':
        raise ValueError(f'{source}: original not downloaded')
    raw = ROOT/'data/raw'/log['filename']
    if sha(raw) != log['sha256']:
        raise ValueError(f'{source}: raw file hash changed')
    path = evidence_file(source, page)
    text = norm(path.read_text(encoding='utf-8'))
    if anchor:
        normalized = norm(anchor)
        if normalized not in text:
            raise ValueError(f'{path.name}: missing anchor {anchor!r}')
        if scope:
            text = text[text.index(normalized):]
    if end and norm(end) in text:
        text = text[:text.index(norm(end))]
    return dict(source_id=source, page=page, path=path, text=text)

def trace(dataset, row, field, original, unit, evidence, converted=None, target_unit=None,
          formula='identity', kind='published_measurement', notes='', required_text=None):
    text = evidence['text']
    if required_text and norm(required_text) not in text:
        raise ValueError(f"{evidence['path'].name}: evidence anchor missing: {required_text}")
    original = str(original)
    # Explicit table transcriptions must have the original number in the inspected text.
    if kind != 'qualitative' and original:
        compact = re.sub(r'\s+', '', text)
        token = re.sub(r'\s+', '', original)
        image_reviews={('S01',127):'serisurvey_2839_review_127.png',('S16',4):'plastics_89308_review_4.png',('S02',76):'gasifier_handbook_3022_review_76.png'}
        visual_name=image_reviews.get((evidence['source_id'],evidence['page']))
        visually_reviewed=bool(visual_name and (ROOT/'data/processed'/visual_name).exists())
        if token not in compact and token.replace(',', '') not in compact.replace(',', '') and not visually_reviewed:
            raise ValueError(f"{evidence['path'].name}: original number {original} missing")
    value = original if converted is None else converted
    row[field] = value
    VERIFICATION.append(dict(source_id=evidence['source_id'], parameter_id=(row['record_id'] if dataset=='conversion_parameters' and field=='value_typical' else row['record_id']+':'+field),
        original_value=original, original_unit=unit, converted_value=value,
        converted_unit=target_unit or unit, evidence_location=f"{evidence['path'].relative_to(ROOT).as_posix()}; {row.get('evidence_location','')}",
        retrieval_status='downloaded', verification_status='verified',
        reviewer_notes='Original evidence inspected by Codex; not independent laboratory validation. '+notes,
        dataset_name=dataset, record_id=row['record_id'], field_name=field,
        conversion_formula=formula, evidence_kind=kind, evidence_file=evidence['path'].relative_to(ROOT).as_posix(),
        evidence_sha256=sha(evidence['path']), raw_sha256=LOGS[evidence['source_id']]['sha256'],
        evidence_text=text, evidence_image='data/processed/'+{('S01',127):'serisurvey_2839_review_127.png',('S16',4):'plastics_89308_review_4.png',('S02',76):'gasifier_handbook_3022_review_76.png'}.get((evidence['source_id'],evidence['page']),'') if (evidence['source_id'],evidence['page']) in [('S01',127),('S16',4),('S02',76)] else '',
        measurement_basis=row.get('measurement_basis', row.get('heating_value_basis',''))))

def base(dataset, source, location, **fields):
    prefix = {'waste_properties':'W', 'technology_mapping':'M', 'conversion_parameters':'P', 'technology_performance':'T'}[dataset]
    rid = f'{prefix}{len(DATA[dataset])+1:04}'
    row = dict(record_id=rid,source_id=source,evidence_location=location,verification_status='verified',**fields)
    if dataset=='waste_properties': row['waste_id']=rid
    if dataset=='conversion_parameters': row['parameter_id']=rid
    return row

def commit(dataset, row):
    DATA[dataset].append(row)

def attempt(label, function, *args):
    before = len(VERIFICATION)
    counts = {name:len(rows) for name,rows in DATA.items()}
    try:
        function(*args)
    except (ValueError, FileNotFoundError, IndexError) as exc:
        del VERIFICATION[before:]
        for name,rows in DATA.items():
            del rows[counts.get(name,0):]
        ISSUES.append({'selection':label,'reason':str(exc)})

def agricultural(page, anchor, end, subtype, category='Agricultural residues'):
    ev=proof('S01',page,anchor,end,scope=True)
    text=ev['text']
    # Known OCR defects in these inspected pages; repairs concern text labels only.
    text=text.replace('t h e ultimate','the ultimate').replace('ash P content','ash content').replace('(gtoss)','(gross)')
    row=base('waste_properties','S01',f'PDF page {page}; {anchor}',waste_category=category,waste_subtype=subtype,
        sample_type='published_reference_record', heating_value_basis='gross q_v; sample moisture basis not explicitly stated',
        proximate_analysis_basis='dry mass', ultimate_analysis_basis='dry mass',
        limitations='Historical compiled reference record; not a universal waste-category average. Net q_v retained separately, not assigned to conventional LHV.')
    prox=text.split('Also the ultimate')[0].split('gross heat')[0]
    number_pattern=r'(\d+(?:\.\d+)?)'
    definitions=[('volatile_matter_pct_dry',r'\(?VCM\)?\s*=?\s*'+number_pattern),('ash_pct_dry',r'ash\s+content\s*=?\s*'+number_pattern),('fixed_carbon_pct_dry',r'fixed\s+carbon\s*=?\s*'+number_pattern)]
    for field,pattern in definitions:
        match=re.search(pattern,prox)
        if not match: raise ValueError(f'{anchor}: cannot parse {field}')
        trace('waste_properties',row,field,match.group(1),'% dry mass',ev,converted=float(match.group(1)))
    if 'ultimate analysis' in text or 'ultimate' in text:
        ultimate=text.split('Also the ultimate')[1].split('gross heat')[0]
        for field,name in [('carbon_pct_dry','carbon'),('hydrogen_pct_dry','hydrogen'),('oxygen_pct_dry','oxygen'),('nitrogen_pct_dry','nitrogen'),('sulfur_pct_dry','sulfur'),('chlorine_pct_dry','chlorine'),('ultimate_ash_pct_dry',r'residue\s*\(ash\)')]:
            match=re.search(name+r'\s*=?\s*'+number_pattern,ultimate)
            if match: trace('waste_properties',row,field,match.group(1),'% dry mass',ev,converted=float(match.group(1)))
    for field,label in [('hhv_mj_kg','gross'),('net_heat_constant_volume_mj_kg','net')]:
        match=re.search(r'q[^\s(]{0,8}\('+label+r'\)\s*=?\s*([\d ]+)\s+[Jf3]\s+g',text)
        if match:
            number=float(match.group(1).replace(' ',''))
            trace('waste_properties',row,field,match.group(1),'J/g',ev,converted=number/1000,target_unit='MJ/kg',formula='x / 1000')
    if 'hhv_mj_kg' not in row: raise ValueError(f'{anchor}: gross heat parse failed')
    if subtype=='Zinfandel vineyard prunings':
        row.update(quality_flag='published_proximate_mass_closure_99_52_pct',model_ready='false',limitations=row['limitations']+' Published proximate fractions sum to 99.52%; retained without correction and excluded from mass-balance-ready subset.')
    commit('waste_properties',row)

AGRICULTURAL = [
 (14,'ALMOND, ORCHARD','ALMOND SHELLS','Almond orchard prunings'),
 (14,'ALMOND SHELLS',None,'Almond shells'),
 (15,'BARLEY STRAW',None,'Barley straw'),
 (16,'BEAN STIRAW','BLACK WALNUT','Bean straw'),
 (16,'BLACK WALNUT',None,'Black walnut orchard prunings'),
 (17,'CABERNET SAUVIGNON','CARDINAL GRAPES','Cabernet Sauvignon vineyard prunings'),
 (17,'CARDINAL GRAPES',None,'Cardinal vineyard prunings'),
 (18,'CHENIN BLANC','COCOA HULLS','Chenin Blanc vineyard prunings'),
 (18,'COCOA HULLS',None,'Cocoa hulls'),
 (19,'COCONUT FIBER','CORN COBS','Coconut fiber dust'),
 (19,'CORN COBS',None,'Corn cobs'),
 (20,'CORN STOVER','COTTON GIN','Corn stover'),
 (20,'COTTON GIN',None,'Cotton gin trash'),
 (21,'COTTON STALKS','ENGLISH WALNUT','Cotton stalks'),
 (21,'ENGLISH WALNUT',None,'English walnut orchard prunings'),
 (22,'GRAPE POMACE',None,'Grape pomace','Industrial organic waste'),
 (24,'OLIVE PITS','PEACH PITS','Olive pits'),
 (24,'PEACH PITS',None,'Peach pits'),
 (25,'PEANUT HULLS','PINOT NOIR','Peanut hulls'),
 (25,'PINOT NOIR',None,'Pinot Noir vineyard prunings'),
 (26,'PISTACHIO SHELLS','PRUNE PITS','Pistachio shells'),
 (26,'PRUNE PITS',None,'Prune pits'),
 (27,'RIBIER GRAPES','RICE HULLS','Ribier vineyard prunings'),
 (28,'RICE STRAW (COLLECTED','RICE STRAW, WEATHERED','Rice straw after harvest'),
 (28,'RICE STRAW, WEATHERED',None,'Rice straw weathered six months'),
 (30,'SUGARCANE BAGASSE; solid; Material is considered','SUGARCANE BAGASSE; solid; Material is fibrous','Sugarcane bagasse'),
 (31,'THOMPSON SEEDLESS','TOKAY GRAPES','Thompson Seedless vineyard prunings'),
 (31,'TOKAY GRAPES',None,'Tokay vineyard prunings'),
 (32,'WALNUT SHELLS','WHEAT DUST','Walnut shells'),
 (32,'WHEAT DUST',None,'Wheat processing dust','Industrial organic waste'),
 (33,'WHEAT STRAW','ZINFANDEL GRAPES','Wheat straw'),
 (33,'ZINFANDEL GRAPES',None,'Zinfandel vineyard prunings'),
 (267,'POPLAR; solid; Material is considered','POPLAR, YELLOW','Poplar biomass','Wood and forestry waste'),
]

def reference_heat(page, anchor, subtype, category, heat, basis, kind='published_reference_material', extra=None):
    ev=proof('S01',page,anchor)
    row=base('waste_properties','S01',f'PDF page {page}; {subtype}',waste_category=category,waste_subtype=subtype,
        heating_value_basis=basis,sample_type=kind,limitations='Reference material properties are not measurements of a mixed or contaminated waste stream.')
    trace('waste_properties',row,'hhv_mj_kg',heat,'J/g',ev,converted=float(heat)/1000,target_unit='MJ/kg',formula='x / 1000')
    for field,value,unit in extra or []:
        trace('waste_properties',row,field,value,unit,ev,converted=float(value))
    commit('waste_properties',row)

def paper_properties():
    for subtype,moisture,vm,fc,ash,heat in [('Junk mail',4.56,73.32,9.03,13.09,14835),('Magazine',4.11,66.39,7.03,22.47,12746),('Newsprint',5.97,81.12,11.48,1.43,19724)]:
        ev=proof('S01',127,subtype.upper())
        row=base('waste_properties','S01',f'PDF page 127 (printed 138); {subtype}',waste_category='Paper and cardboard',waste_subtype=subtype,
            sample_type='published_reference_record',heating_value_basis='dry mass; gross q_v',proximate_analysis_basis='as received; dry fractions derived using measured moisture',
            ultimate_analysis_basis='not explicitly stated; excluded from dry columns')
        for field,value in [('moisture_pct',moisture),('volatile_matter_pct_as_received',vm),('fixed_carbon_pct_as_received',fc),('ash_pct_as_received',ash)]:
            trace('waste_properties',row,field,str(value),'% as received mass',ev,converted=value,notes='OCR spacing visually checked against original rendered page.')
        trace('waste_properties',row,'total_solids_pct',str(moisture),'% as received moisture',ev,converted=round(100-moisture,8),target_unit='% as received mass',formula='100 - x')
        for field,value in [('volatile_matter_pct_dry',vm),('fixed_carbon_pct_dry',fc),('ash_pct_dry',ash)]:
            trace('waste_properties',row,field,str(value),'% as received mass',ev,converted=round(value*100/(100-moisture),8),target_unit='% dry mass',formula=f'x * 100 / (100 - {moisture})',notes='Moisture measured in same published sample; no cross-sample combination.')
        trace('waste_properties',row,'hhv_mj_kg',str(heat),'J/g dry',ev,converted=heat/1000,target_unit='MJ/kg dry',formula='x / 1000',notes='Dry-basis column visually inspected; OCR unit artifacts corrected using rendered original.')
        commit('waste_properties',row)

def ad_feed_properties():
    ev=proof('S03',34,'Table 3.5.')
    for regime,day,ts,vs in [('thermophilic',15,9.3,87),('thermophilic',10,9.8,90.6),('mesophilic',15,6.4,86.3),('mesophilic',10,9.6,89.9)]:
        row=base('waste_properties','S03',f'Table 3.5, PDF page 34, Feed {regime}, {day}-day MCRT',waste_category='Food and organic waste',waste_subtype=f'EBMUD food waste pulp; {regime}; {day}-day MCRT',
            sample_type='experimental_period_feed_mean',heating_value_basis='not measured',solids_basis='TS % wet feed; VS % TS',limitations='Diluted preprocessed pulp at digester inlet; not raw delivered food waste.')
        trace('waste_properties',row,'total_solids_pct',str(ts),'% wet feed mass',ev,converted=ts)
        trace('waste_properties',row,'volatile_solids_pct_ts',str(vs),'% total solids',ev,converted=vs)
        commit('waste_properties',row)
    row=base('waste_properties','S03','Table 3.5, PDF page 34, municipal wastewater solids Feed',waste_category='Sewage sludge',waste_subtype='EBMUD primary sludge and thickened waste activated sludge feed',sample_type='previous_bench_study_feed_mean',heating_value_basis='not measured',solids_basis='TS % wet feed; VS % TS')
    trace('waste_properties',row,'total_solids_pct','4.0','% wet feed mass',ev,converted=4.0)
    trace('waste_properties',row,'volatile_solids_pct_ts','77.0','% total solids',ev,converted=77.0)
    commit('waste_properties',row)

def conversion(source,page,anchor,subtype,technology,name,low,typical,high,unit,basis,conditions,kind='experimental_measurement',notes='',factor=None):
    ev=proof(source,page,anchor)
    row=base('conversion_parameters',source,f'PDF page {page}; {anchor}' if page else anchor,waste_subtype=subtype,technology=technology,parameter_name=name,unit=unit,measurement_basis=basis,operating_conditions=conditions,evidence_kind=kind,limitations=notes)
    for field,value in [('value_min',low),('value_typical',typical),('value_max',high)]:
        if value is not None:
            trace('conversion_parameters',row,field,str(value),('degF' if factor=='fahrenheit' else unit),ev,
                converted=round((float(value)-32)*5/9,8) if factor=='fahrenheit' else value,
                target_unit=unit,formula='(x - 32) * 5 / 9' if factor=='fahrenheit' else 'identity',kind=kind,notes=notes)
    commit('conversion_parameters',row)

def parameters():
    for subtype,day,low,avg,high,basis in [('EBMUD food waste pulp',15,300,420,530,'dry metric tonne TS applied'),('EBMUD food waste pulp',10,200,300,450,'dry metric tonne TS applied'),('EBMUD municipal wastewater solids',15,230,310,390,'dry metric tonne TS applied'),('EBMUD source-separated delivered food waste',15,75,100,135,'wet metric tonne delivered before processing'),('EBMUD source-separated delivered food waste',10,50,75,110,'wet metric tonne delivered before processing')]:
        conversion('S03',48,'Table 3.11.',subtype,'Anaerobic digestion','Methane production yield',low,avg,high,'m3 CH4/t',basis,f'{day}-day MCRT; stable operating periods; combined mesophilic and thermophilic observations',notes='Methane, not biogas. Gas reference temperature and pressure not explicitly stated; not relabeled Nm3. Report-rounded yields retained. Sludge is a previous-study comparator.')
    for regime,day,gas,methane,vsd,loading in [('mesophilic',15,4.0,64,73.8,0.22),('thermophilic',15,4.8,67,80.8,0.35),('mesophilic',10,4.5,59,76.4,0.53),('thermophilic',10,5.4,60,82.4,0.55)]:
        conditions=f'30 L bench digester; {regime}; {day}-day MCRT; food waste pulp'
        for page,anchor,name,value,unit,basis in [(28,'Table 3.4.','Biogas production rate',gas,'L biogas/h','total gas volume per reactor time; reference T/P unspecified'),(41,'Table 3.9.','Methane concentration in biogas',methane,'%','volume fraction CH4 in biogas'),(39,'Table 3.7.','Volatile solids destruction',vsd,'%','volatile solids removed / volatile solids fed'),(38,'Table 3.6.','Volatile solids loading rate',loading,'lb VS/ft3/day','volatile solids feed per reactor volume per day')]:
            conversion('S03',page,anchor,'EBMUD food waste pulp','Anaerobic digestion',name,None,value,None,unit,basis,conditions,notes='Published average. Standard deviation is not a min/max bound; stable 15/10-day periods only.')
    for mode,temp,values,conditions in [('fast',500,[75,12,13],'hot vapour residence approximately 1 s'),('intermediate',500,[50,20,30],'hot vapour residence approximately 10-20 s'),('slow carbonisation',400,[30,35,35],'very long solids residence time')]:
        for name,value in zip(['Liquid product yield','Char product yield','Gas product yield'],values):
            conversion('S07',5,'Table 1: Typical','Dry wood reference','Pyrolysis',name,None,value,None,'% dry feed mass','dry wood mass',f'{mode}; around {temp} degC; {conditions}',kind='documented_reference_typical',notes='Reference typical yields, not an equipment-specific experiment; liquid includes water. Do not infer electricity efficiency.')
    conversion('S02',43,'5.7.3','Wood-fuelled Imbert reference','Gasification','Producer gas heating value',None,6.1,None,'MJ/Nm3','normal gas volume at 0 degC and 1 atm; HHV/LHV unspecified here','Imbert gasifier hearth-sizing example',kind='documented_reference_typical',notes='Illustrative gas energy content, not electricity or measured generic plant efficiency.')
    conversion('S02',25,'3.4.1','Densified biomass residues','Gasification','Densification auxiliary energy',1,None,2,'% feedstock energy','energy consumed / energy contained in biomass','pellet or cube pretreatment; drying additional',kind='documented_reference_range')
    conversion('S19',10,'Integrated bench-scale','Deacetylated corn stover','Fermentation','Cellulose-to-ethanol yield',None,87,None,'% theoretical cellulose-to-ethanol yield','cellulose-to-ethanol integrated yield; not total feed mass','whole slurry; 20% TS; 40 mg enzyme protein/g cellulose; bench hydrolysis and fermentation after pilot pretreatment',notes='Measured achievement, not the adjacent 86% design target.')
    conversion('S19',10,'Integrated bench-scale','Deacetylated corn stover','Fermentation','Xylose-to-ethanol yield',None,94,None,'% theoretical xylose-to-ethanol yield','xylose-to-ethanol yield; not total feed mass','whole slurry; 20% TS; bench-scale fermentation',notes='Measured achievement, not adjacent 85% design target.')
    for run,xylose,arabinose,cellulose in [(2,86.2,61.6,84.0),(3,66.1,55.9,82.7),(4,92.6,54.1,74.4),(5,91.3,50.9,78.3)]:
        for name,value,basis in [('Pilot xylose-to-ethanol yield',xylose,'ethanol remaining after accounting for ethanol from glucose and arabinose'),('Pilot arabinose-to-ethanol yield',arabinose,'arabinose utilization multiplied by assumed 95% metabolic yield'),('Pilot cellulose-to-ethanol yield',cellulose,'calculated assuming constant 95% glucose-to-ethanol yield')]:
            conversion('S19',24,'Table 8.','Deacetylated corn stover, pilot demonstration run '+str(run),'Fermentation',name,None,value,None,'%',basis,'FY2012 pilot demonstration run '+str(run)+'; integrated pretreatment/hydrolysis/fermentation',kind='published_calculated_from_experiment',notes='Published experimental accounting calculation, not direct total-feed mass yield. '+('Run 3 had contamination reducing fermentation yields; retain as observed, not an optimal design recommendation.' if run==3 else 'Run 1 omitted because fermentation yield was not reported.'))
    conversion('S09',37,'Counter current acid esterification','Pure fatty acid streams','Biodiesel production','Fatty acid methyl ester yield lower threshold',99,None,None,'%','methyl ester yield; mass/molar basis not explicitly stated','counter-current acid esterification; pure fatty acid stream; water removed',kind='documented_reference_bound',notes='Strictly above 99%, so value_min is an open lower threshold; not a measured used-cooking-oil biodiesel yield.')
    DATA['conversion_parameters'][-1]['value_min_inclusive']='false'
    for subtype,low,high in [('Furnace/heating exhaust gases',600,2000),('Gas turbine exhaust gases',900,1100),('Engine jacket cooling water',190,200),('Compressor post-intercooler water',100,180),('Hot products',200,2500),('Steam vents or leaks',250,600),('Condensate',150,500)]:
        conversion('S15',3,'Table 6.M.1',subtype,'Industrial waste heat recovery','Waste heat source temperature',low,None,high,'degC','source stream temperature; not reactor temperature or recoverable-energy efficiency','reference ranges; cleanliness and corrosiveness determine recovery design',kind='documented_reference_range',factor='fahrenheit')

def additional_experiments():
    # Table 7-8 gasification runs, visually inspected by run and column. No mean row
    # is added because it would double-count the same experiments.
    runs=[('98',26.7,16.52,5.33,2.22,3.28,70.2),('910',26.7,16.52,5.18,2.28,3.21,70.2),('920',33.6,6.01,5.33,2.48,4.06,78.1),('927',41.2,8.11,5.63,2.54,3.08,85.0),('922',47.8,5.75,5.44,1.43,2.76,46.1),('101',48.7,6.99,5.59,2.18,3.45,72.5),('929',48.8,7.41,5.63,2.10,3.72,70.2),('1011',49.5,7.31,5.44,2.55,3.94,82.2),('1015',52.3,7.95,5.33,2.73,4.69,86.3),('924',53.7,5.50,5.66,1.62,2.79,54.2),('106',54.3,6.67,5.48,1.95,2.18,63.5),('123',54.3,14.61,5.51,1.90,4.27,62.1),('104',63.7,7.72,5.55,2.61,2.71,86.2),('1129',68.9,14.27,5.59,2.85,3.82,94.4),('121',72.5,15.07,5.63,1.39,3.57,46.5),('1119',74.6,16.32,5.74,2.11,3.96,71.8),('1117',85.4,11.26,5.78,2.30,2.92,79.1),('1110',119.7,11.56,5.74,1.79,1.67,60.8),('1221',125.5,10.67,5.44,2.10,3.25,67.9)]
    for run,rate,moisture,hhv,yield_,char,cge in runs:
        conditions=f'Table 7-8 run {run}; dry chip rate {rate} kg/h; chip moisture {moisture}% wet basis; temperature not given in table'
        for name,value,unit,basis in [('Dry producer gas HHV',hhv,'MJ/m3','dry gas; gas reference temperature/pressure not stated in table'),('Dry producer gas volume yield',yield_,'m3 gas/kg dry chips','dry chips denominator; dry gas volume; reference temperature/pressure not stated in table'),('Char mass yield',char,'% dry chip mass','kg char per 100 kg dry chips'),('Cold gas efficiency',cge,'% HHV','energy in gas / energy in wood')]:
            conversion('S02',76,'Table 7','Wood chips, Walawender 1985 run '+run,'Gasification',name,None,value,None,unit,basis,conditions,kind='published_experimental_table',notes='Run/column assignment visually inspected in rendered original; cited experiment reproduced by NREL handbook. Temperature and gas normalization require primary-paper follow-up.')
    for name,value,unit,basis in [('Biocrude oil yield',44,'% dry ash-free feed mass','dry ash-free sludge; recovered after separations'),('Aqueous product yield',31,'% dry ash-free feed mass','dry ash-free sludge; recovered after separations'),('Gas product yield',16,'% dry ash-free feed mass','dry ash-free sludge; recovered after separations'),('Solid product yield',9,'% dry ash-free feed mass','dry ash-free sludge; recovered after separations'),('Reactor residence time',17,'min','equivalent residence time'),('HTL pressure',20.5,'MPa','absolute reactor pressure')]:
        conversion('S20',28,'Table 5.','Detroit 50/50 primary/secondary sludge; WW06 SS-2','Hydrothermal conversion',name,None,value,None,unit,basis,'347 degC; 20.5 MPa; feed 20 wt% solids including ash; continuous hybrid CSTR-PFR; LHSV 3.6/h',notes='Experimental results column only. Adjacent goal-case assumptions intentionally excluded. Sludge-derived oil HHV is calculated by Boie equation, not a bomb-calorimetry observation.')
    # Exact sample identities and CH measurements from the open peer-reviewed Table 1.
    ev=proof('S16',4,'Table')
    for subtype,c,h in [('PP-1',82.41,13.73),('PP-2',85.62,13.65),('PP-3',85.05,13.47),('PP-4',85.63,13.74),('PP-5',85.70,12.85),('PP-6',84.93,13.35),('PP-7',84.93,13.90),('PVC-1',38.21,3.97),('PVC-2',38.56,3.90),('PS-1',91.66,8.33),('PS-2',91.57,8.26),('PS-3',90.97,7.22),('PS-4',91.84,7.27),('PS-5',91.61,7.26),('PU-1',65.77,10.06)]:
        row=base('waste_properties','S16',f'Table 1 continued, PDF page 4; sample {subtype}',waste_category='Plastics',waste_subtype='Commercial reference polymer '+subtype,
            sample_type='peer_reviewed_commercial_reference_sample',sample_identifier=subtype,
            heating_value_basis='not measured',ultimate_analysis_basis='as measured CHNS; dry basis not explicitly stated',
            limitations='Commercial research polymer; not a post-consumer waste measurement. CHNS values retained as measured, not assigned to dry-basis columns.')
        trace('waste_properties',row,'carbon_pct_as_measured',str(c),'% sample mass as measured',ev,converted=c,notes='Sample row visually inspected in original Table 1.')
        trace('waste_properties',row,'hydrogen_pct_as_measured',str(h),'% sample mass as measured',ev,converted=h,notes='Sample row visually inspected in original Table 1.')
        commit('waste_properties',row)

def htl_feed_and_mapping():
    ev=proof('S20',24,'Table 4.')
    row=base('waste_properties','S20','Table 4, PDF page 24; experimental dry-basis column',waste_category='Sewage sludge',waste_subtype='Detroit 50/50 primary/secondary sludge, experimental feed',sample_type='experimental_sludge_reference',heating_value_basis='not measured; source HHV calculation excluded',ultimate_analysis_basis='dry mass; source experimental column',quality_flag='published_ultimate_analysis_mass_closure_exceeds_100_pct',limitations='Source-reported dry elemental fractions plus ash exceed 100%; preserved without normalization. Exclude from closed mass-balance modeling until clarified.',model_ready='false')
    for field,value in [('carbon_pct_dry',41.06),('hydrogen_pct_dry',5.67),('oxygen_pct_dry',26.06),('nitrogen_pct_dry',4.98),('sulfur_pct_dry',1.03),('ash_pct_dry',26.08),('phosphorus_pct_dry',1.86)]: trace('waste_properties',row,field,str(value),'% dry mass',ev,converted=value,notes='Experimental column; do not substitute modeled 15% ash. Published mass closure discrepancy retained and flagged.')
    commit('waste_properties',row)
    mapping('S20',27,'experimental testing','Sewage sludge','50/50 primary/secondary sewage sludge','Hydrothermal conversion','biocrude; fuel blendstocks after upgrading','demonstrated','Qualified high-pressure continuous HTL; aqueous stream treatment; biocrude upgrading','Sludge conditioning and dewatering to experimental solids content','347 degC/20.5 MPa experimental conditions; do not treat modeled goal-case performance as observations.',restriction='Pressure equipment, wastewater discharge, contaminants and solids disposal review')

def phyllis_properties():
    from bs4 import BeautifulSoup
    for source,number,subtype,category in [('S28',2782,'Dairy cow manure mechanically conditioned; Phyllis #2782','Animal manure'),('S29',957,'Fresh chicken manure; Phyllis #957','Animal manure'),('S30',1528,'Dairy cow manure with straw bedding; Phyllis #1528','Animal manure'),('S31',3491,'Animal fat co-combustion product Rotterdam; Phyllis #3491','Used cooking oil and fats')]:
        ev=proof(source,None,'Values')
        sourcefile=ROOT/'data/raw'/LOGS[source]['filename']
        soup=BeautifulSoup(sourcefile.read_bytes(),'html.parser')
        row=base('waste_properties',source,f'Phyllis2 sample #{number}; public Values table, ar/dry/daf headers',waste_category=category,waste_subtype=subtype,sample_type='individual_database_reference_record',sample_identifier=str(number),
            heating_value_basis='dry mass' if number in [2782,3491] else 'not measured',
            ultimate_analysis_basis='dry mass; Phyllis dry column',proximate_analysis_basis='ash dry column; moisture as received',
            source_record_url=f'https://phyllis.nl/Biomass/View/{number}',limitations='Individual public database record. XLSX export requires login and was not used; source-specific literature/methods remain in archived HTML.')
        definitions={'Ash content':'ash_pct_dry','Carbon':'carbon_pct_dry','Hydrogen':'hydrogen_pct_dry','Oxygen':'oxygen_pct_dry','Nitrogen':'nitrogen_pct_dry','Sulphur':'sulfur_pct_dry','Gross calorific value (HHV)':'hhv_mj_kg','Net calorific value (LHV)':'lhv_mj_kg'}
        for tr in soup.find_all('tr'):
            label=tr.find('td',colspan='9')
            if not label: continue
            label=label.get_text(' ',strip=True)
            numbers=[td.get_text(' ',strip=True) for td in tr.find_all('td',class_='number')]
            if label=='Moisture content':
                if numbers and numbers[0]:
                    trace('waste_properties',row,'moisture_pct',numbers[0],'% as received mass',ev,converted=float(numbers[0]),notes='Actual public HTML water-value cell, not standard deviation or detection limit.')
                    trace('waste_properties',row,'total_solids_pct',numbers[0],'% as received moisture',ev,converted=round(100-float(numbers[0]),8),target_unit='% as received mass',formula='100 - x')
            elif label in definitions and len(numbers)>1 and numbers[1]:
                # The first three numeric cells are ar, dry and daf, as inspected in DOM.
                field=definitions[label]
                calculated=number==1528 and label=='Carbon'
                unit='MJ/kg dry mass' if field.endswith('_mj_kg') else '% dry mass'
                trace('waste_properties',row,field,numbers[1],unit,ev,converted=float(numbers[1]),kind='published_calculated' if calculated else 'database_reference_measurement',notes='Public dry-basis table cell. '+('Carbon calculated from C/N by source, not independently measured.' if calculated else 'Source measurement/method notes retained in raw HTML.'))
                if calculated: row['carbon_measurement_status']='calculated by source from C/N ratio'
        commit('waste_properties',row)

def performance():
    # Original tables distinguish nominal and net electrical output and fuel-energy basis.
    ev=proof('S04',36,'Table 2-2.')
    thermal_ev=proof('S04',37,'Table 2-2.')
    systems=[('Tecogen Inverde Ultra 100',100,27.0,53.0),('GE Jenbacher JMS-312C65',633,34.5,44.4),('GE Jenbacher JMS-416B85',1121,36.8,41.6),('GE Jenbacher JMS-620F01',3326,40.4,37.9),('Wartsila 20V34SG',9341,41.6,35.0)]
    for name,capacity,electrical,thermal in systems:
        row=base('technology_performance','S04',f'Table 2-2, PDF pages 36-37; {name}',technology_name='Combined heat and power',equipment_type=name+' natural-gas spark ignition engine',capacity_unit='kW electrical baseload',efficiency_basis='HHV fuel input',required_feedstock_conditions='Natural gas in source table. Waste-derived biogas requires manufacturer qualification and gas cleanup; source efficiencies are not guaranteed for biogas.',applicable_scale='commercial baseload engine',fuel_type='natural gas',operating_conditions='Representative commercial gensets available in 2013; baseload ratings; recovered hot water',limitations='Equipment reference only; not direct solid-waste conversion efficiency.')
        for field,value in [('capacity',capacity),('electrical_efficiency_pct',electrical)]: trace('technology_performance',row,field,str(value),'kW electrical' if field=='capacity' else '% HHV',ev,converted=value,kind='equipment_reference',notes='Source comma thousands separators normalized.')
        trace('technology_performance',row,'thermal_efficiency_pct',str(thermal),'% HHV',thermal_ev,converted=thermal,kind='equipment_reference')
        commit('technology_performance',row)
    ev=proof('S04',98,'Table 5-2.')
    for name,nominal,capacity,parasitic,electrical in [('Capstone C30',30,28,2,21.9),('Capstone C65 CARB',65,61,4,23.7),('Capstone C200 CARB',200,190,10,26.6),('FlexEnergy MT250',250,240,10,26.0),('FlexEnergy MT330',333,320,13,28.0),('Capstone C1000-LE',1000,950,50,26.6)]:
        row=base('technology_performance','S04',f'Table 5-2, PDF pages 98-99; {name}',technology_name='Combined heat and power',equipment_type=name+' microturbine',capacity_unit='kW net electrical',auxiliary_energy_unit='kW electrical compressor power',efficiency_basis='HHV; net of gas booster compressor',required_feedstock_conditions='Natural gas; 1 psi inlet supply requiring gas booster; waste gas operation requires separate manufacturer qualification.',applicable_scale='commercial microturbine',fuel_type='natural gas',operating_conditions='Full load ISO conditions: 59 degF, 60% RH, 14.7 psia',limitations='Auxiliary column is power, not energy per mass feed. Thermal efficiency left blank because table reports total CHP efficiency rather than a separate thermal efficiency.')
        for field,value,unit in [('capacity',capacity,'kW net electrical'),('nominal_capacity',nominal,'kW electrical'),('auxiliary_energy_consumption',parasitic,'kW electrical'),('electrical_efficiency_pct',electrical,'% HHV')]: trace('technology_performance',row,field,str(value),unit,ev,converted=value,kind='equipment_reference')
        commit('technology_performance',row)
    ev=proof('S03',18,'Two 30-L acrylic digesters')
    for regime,temp in [('mesophilic',35),('thermophilic',50)]:
        row=base('technology_performance','S03','Section 2, PDF page 18',technology_name='Anaerobic digestion',equipment_type=f'EBMUD {regime} acrylic bench digester',capacity_unit='L reactor volume',required_feedstock_conditions='Preprocessed EBMUD food waste pulp; semcontinuous feed; continuous mixing; tested 15-,10-,5-day MCRT',applicable_scale='bench experimental',operating_conditions='Water bath with circulating immersion heater',limitations='5-day MCRT became unstable; temperature is target, not period mean; auxiliary electrical demand not measured.')
        trace('technology_performance',row,'capacity','30','L reactor volume',ev,converted=30)
        trace('technology_performance',row,'operating_temperature_c',str(temp),'degC target',ev,converted=temp)
        commit('technology_performance',row)

def mapping(source,page,anchor,category,subtype,technology,outputs,status,conditions,preprocess,limitations,hazard='false',restriction=''):
    ev=proof(source,page,anchor)
    row=base('technology_mapping',source,f'PDF page {page}; {anchor}' if page else anchor,waste_category=category,waste_subtype=subtype,technology=technology,possible_energy_outputs=outputs,feasibility_status=status,required_conditions=conditions,preprocessing_required=preprocess,limitations=limitations,hazard_flag=hazard,regulatory_restrictions=restriction,evidence_kind='documented_qualitative')
    trace('technology_mapping',row,'mapping_evidence',anchor,'qualitative',ev,kind='qualitative',notes='Qualitative applicability only; no numerical yield implied.',required_text=anchor)
    commit('technology_mapping',row)

def mappings():
    for category,subtype,anchor in [('Food and organic waste','Source-separated food waste','Food waste'),('Animal manure','Animal manures','Animal manures'),('Sewage sludge','Wastewater solids','Wastewater solids'),('Industrial organic waste','Industrial organic residuals','Industrial organic residuals'),('Used cooking oil and fats','Fats, oils, and greases','Fats, oils, and greases'),('Agricultural residues','Biodegradable crop residue','crop residue')]:
        mapping('S05',None,anchor,category,subtype,'Anaerobic digestion','biogas','conditional','Biodegradable organic fraction; qualified digester design and loading; anaerobic conditions','Remove contaminants; characterize inhibitory compounds','Gas yield depends on actual feed composition; not all crop residues readily digestible.',restriction='Site permits and digestate handling requirements must be checked locally')
    for category,subtype in [('Food and organic waste','Biogas from food waste digestion'),('Animal manure','Biogas from manure digestion'),('Sewage sludge','Biogas from wastewater solids digestion')]:
        mapping('S05',None,'including combined heat and power systems',category,subtype,'Combined heat and power','electricity; useful heat','conditional','First digest feedstock; capture biogas; use compatible gas engine','Remove gas contaminants to equipment specifications','Indirect biogas-to-CHP route; equipment efficiencies are fuel-specific.',restriction='Air permits and gas safety requirements')
    for subtype,anchor in [('Corn cobs','corn cobs'),('Chipped or densified biomass residues','straw'),('Wood chips and mill ends','mill ends')]:
        mapping('S02',24,anchor,'Wood and forestry waste' if 'Wood' in subtype else 'Agricultural residues',subtype,'Gasification','producer gas','conditional','Fuel-specific gasifier trials; controlled particle size and ash behaviour','Chipping/chopping or densification; remove fines and dirt','Ash slagging, tar, CO toxicity and combustible gas hazards; not a universal feedstock route.',restriction='Permitted industrial equipment and emissions controls')
    for category,subtype,anchor in [('Wood and forestry waste','Clean wood and bark','bark'),('Agricultural residues','Straw and nut shells','straw'),('Sewage sludge','Dried sewage sludge','sewage sludge'),('Textile waste','Leather waste reference','leather wastes')]:
        mapping('S07',6,anchor,category,subtype,'Pyrolysis','bio-oil; char; fuel gas','conditional','Controlled oxygen-free industrial reactor; confirm contamination and product suitability','Drying and size reduction as specified by reactor','Qualitative tested-feedstock evidence; generic wood yields cannot be transferred to these waste types.',restriction='Emissions control; contaminated sludge/leather requires contaminant assessment')
    mapping('S19',10,'corn stover','Agricultural residues','Corn stover','Fermentation','ethanol','demonstrated','Pretreatment, enzymatic hydrolysis and qualified fermenting organism','Deacetylation; acid pretreatment; hydrolysis','Published integrated bench results; whole biomass is not directly fermentable.')
    mapping('S09',35,'Yellow greases','Used cooking oil and fats','Yellow grease','Biodiesel production','fatty acid methyl esters','conditional','Characterize FFA, water and contaminants; appropriate catalyst process','High-FFA pretreatment; water removal; product purification','Pure fatty acid esterification threshold is not a yellow-grease measured yield.',restriction='Fuel quality and chemical process safety requirements')
    mapping('S10',None,'non-recyclable','Municipal solid waste','Non-recyclable non-hazardous MSW','Combustion','heat; electricity','conditional','Confined controlled waste combustor and energy recovery','Sorting; recover recyclable metals; control feed quality','Ash characterization and safe disposal; source reduction and recycling rank ahead of energy recovery.',restriction='Applicable air emissions standards; ash hazardous-waste determination')
    mapping('S10',None,'refuse derived fuel','Municipal solid waste','Combustible RDF fraction','RDF/SRF production','solid recovered fuel','conditional','Specified fraction separation and downstream compatible permitted combustor','Shredding; remove noncombustibles','RDF manufacturing is fuel preparation; it does not itself generate electricity.',restriction='Non-hazardous fuel classification and applicable emissions standards')
    mapping('S11',None,'electricity','Landfill waste','Biodegradable waste already in MSW landfill','Landfill gas recovery','landfill gas; electricity; heat; upgraded fuel','conditional','Engineered gas collection and site-specific gas treatment','Gas collection wells; moisture and contaminant removal','Recovery from existing decomposition; not a recommendation to landfill recyclable organics.',restriction='Landfill gas collection, emissions and safety requirements')
    mapping('S15',5,'heat quantity','Industrial waste heat','Industrial hot gases and liquids','Industrial waste heat recovery','useful heat; electricity where viable','conditional','Evaluate heat quantity, temperature, composition, sink and schedules','Suitable heat exchangers; fouling and corrosion control','Losses are not all recoverable; no generic conversion efficiency applied.')
    mapping('S17',None,'Medical Waste Incineration','Hazardous and medical waste','Regulated medical waste','Combustion','','restricted','Specialist authorized treatment facility only; site-specific regulatory review','Segregation; infectious/sharps handling according to competent authority','Treatment evidence only; energy recovery is not established by this source. Never route into ordinary organic or MSW equipment.',hazard='true',restriction='Medical waste rules and HMIWI air standards; local jurisdiction review required')

def main():
    global LOGS
    LOGS=load_logs()
    for args in AGRICULTURAL: attempt(args[3],agricultural,*args)
    for args in [
        (167,'POLYETHYLENE','PE SRM 1475, 72% crystallinity','Plastics',46332.4,'reference polymer as tested; gross q_v at 25 degC'),
        (168,'POLYETHYLENE','PE sample 1, high-pressure polymer','Plastics',46415.6,'reference polymer as tested; gross q_v at 25 degC'),
        (168,'POLYETHYLENE','PE sample 2, linear Marlex','Plastics',46362.5,'reference polymer as tested; gross q_v at 25 degC'),
        (168,'POLYETHYLENE','PE sample 3, low density','Plastics',46202.7,'reference polymer as tested; gross q_v at 25 degC'),
        (168,'POLYETHYLENE','PE sample 4, high density Mirathen H','Plastics',46485.5,'reference polymer as tested; gross q_v at 25 degC'),
        (169,'POLYPROPYLENE','PP isotactic, 58% crystallinity','Plastics',46368.8,'reference polymer as tested; gross q_v at 25 degC'),
        (169,'POLYPROPYLENE','PP VK 166 untangled','Plastics',46112.7,'reference polymer as tested; gross q_v at 25 degC'),
        (169,'POLYPROPYLENE','PP degree of polymerization approximately 4000','Plastics',46360.8,'reference polymer as tested; gross q_v at 25 degC'),
        (169,'POLYSTYRENE','PS isotactic, 40% crystallinity','Plastics',41463.0,'reference polymer as tested; gross q_v at 25 degC'),
        (169,'POLYSTYRENE','PS isotactic amorphous','Plastics',41499.0,'reference polymer as tested; gross q_v at 25 degC'),
        (169,'POLYSTYRENE','PS atactic amorphous','Plastics',41510.3,'reference polymer as tested; gross q_v at 25 degC'),
        (170,'POLYVINYL CHLORIDE','PVC 99.7 mole percent purity','Plastics',18304.3,'reference polymer as tested; gross q_v per monomer mass at 25 degC'),
        (182,'REFUSE; solid;','Dry shredded garbage sample A','Municipal solid waste',18500,'dry sample; gross q_v'),
        (182,'REFUSE; solid;','Dry shredded garbage sample B','Municipal solid waste',19850,'dry sample; gross q_v'),
        (182,'REFUSE; solid;','Dry shredded garbage sample C','Municipal solid waste',20040,'dry sample; gross q_v'),
        (182,'REFUSE; solid;','Dry shredded garbage sample D','Municipal solid waste',20050,'dry sample; gross q_v'),
        (264,'PINE, PONDEROSA; HEARTWOOD','Ponderosa pine heartwood lumber','Wood and forestry waste',20970,'dry ash-free; gross q_v'),
        (264,'PINE, PONDEROSA; MT 77','Ponderosa pine MT77 foliage','Wood and forestry waste',22400,'dry ash-free; gross q_v'),
        (264,'PINE, PONDEROSA; MT 78','Ponderosa pine MT78 foliage','Wood and forestry waste',22270,'dry ash-free; gross q_v'),
        (266,'PINE, WESTERN WHITE','Western white pine dead foliage','Wood and forestry waste',21760,'dry ash-free; gross q_v'),
    ]: attempt(args[2],reference_heat,*args)
    attempt('paper samples',paper_properties)
    attempt('AD feed samples',ad_feed_properties)
    attempt('conversion tables',parameters)
    attempt('additional experiments',additional_experiments)
    attempt('equipment performance',performance)
    attempt('technology mappings',mappings)
    attempt('HTL feed and mapping',htl_feed_and_mapping)
    attempt('Phyllis public records',phyllis_properties)
    # Sources remain a catalog of attempted sources, including failed retrievals.
    manifest=json.loads((ROOT/'scripts/source_manifest.json').read_text(encoding='utf-8'))
    used={r['source_id'] for rows in DATA.values() for r in rows}
    for source in manifest:
        log=LOGS.get(source['source_id'],{})
        DATA['sources'].append({**{k:source.get(k,'') for k in SCHEMAS['sources']},
            'dataset_filename':('data/raw/'+source['filename']) if log.get('retrieval_status')=='downloaded' else '',
            'access_date':log.get('access_date',''), 'retrieval_status':log.get('retrieval_status','not_attempted'),
            'verification_status':'verified' if source['source_id'] in used else 'not_used_as_record_evidence',
            'sha256':log.get('sha256',''),'final_url':log.get('final_url',''),'records_use_source':str(source['source_id'] in used).lower()})
    for source in manifest:
        log=LOGS.get(source['source_id'],{})
        if source['source_id'] not in used:
            VERIFICATION.append(dict(source_id=source['source_id'],parameter_id='',original_value='',original_unit='',converted_value='',converted_unit='',evidence_location='',retrieval_status=log.get('retrieval_status','not_attempted'),verification_status='not_verified',reviewer_notes=log.get('error','Downloaded discovery/context source; no measurement or mapping curated from it.'),dataset_name='sources',record_id=source['source_id'],field_name='retrieval'))
    DATA['source_verification']=VERIFICATION
    for name in SCHEMAS: write_csv(name,DATA[name])
    (ROOT/'data/processed/build_issues.json').write_text(json.dumps(ISSUES,indent=2),encoding='utf-8')
    print(json.dumps({name:len(DATA[name]) for name in SCHEMAS},indent=2))
    print('Curated selection failures:',json.dumps(ISSUES,indent=2))

if __name__=='__main__': main()
