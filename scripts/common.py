"""Shared schemas, paths, and traceability helpers (stdlib only)."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
 'waste_properties': 'waste_id,waste_category,waste_subtype,moisture_pct,total_solids_pct,volatile_solids_pct_ts,ash_pct_dry,volatile_matter_pct_dry,fixed_carbon_pct_dry,carbon_pct_dry,hydrogen_pct_dry,oxygen_pct_dry,nitrogen_pct_dry,sulfur_pct_dry,hhv_mj_kg,lhv_mj_kg,heating_value_basis,source_id',
 'technology_mapping': 'waste_category,waste_subtype,technology,possible_energy_outputs,feasibility_status,required_conditions,preprocessing_required,limitations,source_id',
 'conversion_parameters': 'parameter_id,waste_subtype,technology,parameter_name,value_min,value_typical,value_max,unit,measurement_basis,operating_conditions,source_id,evidence_location',
 'technology_performance': 'technology_name,equipment_type,capacity,electrical_efficiency_pct,thermal_efficiency_pct,operating_temperature_c,required_feedstock_conditions,auxiliary_energy_consumption,applicable_scale,source_id',
 'sources': 'source_id,organization,publication_title,publication_year,source_url,doi,dataset_filename,license,access_date',
 'source_verification': 'source_id,parameter_id,original_value,original_unit,converted_value,converted_unit,evidence_location,retrieval_status,verification_status,reviewer_notes',
}
SCHEMAS = {k:v.split(',') for k,v in SCHEMAS.items()}
CATEGORIES = ['Food and organic waste','Agricultural residues','Animal manure','Wood and forestry waste','Paper and cardboard','Plastics','Textile waste','Municipal solid waste','Sewage sludge','Industrial organic waste','Used cooking oil and fats','Landfill waste','Industrial waste heat','Hazardous and medical waste','Inert waste']
TECHNOLOGIES = ['Anaerobic digestion','Combustion','Combined heat and power','Gasification','Pyrolysis','RDF/SRF production','Fermentation','Biodiesel production','Hydrothermal conversion','Landfill gas recovery','Industrial waste heat recovery']

def read_csv(name):
    with (ROOT/'data'/f'{name}.csv').open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)

def write_csv(name, rows):
    columns = SCHEMAS[name] + sorted({k for r in rows for k in r} - set(SCHEMAS[name]))
    with (ROOT/'data'/f'{name}.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

def norm(text):
    return re.sub(r'\s+', ' ', text).strip()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_logs():
    return {r['source_id']:r for r in json.loads((ROOT/'data/raw/retrieval_log.json').read_text(encoding='utf-8'))}

def evidence_file(source, page=None):
    return ROOT/'data/processed'/(f'{source}_page_{page:03}.txt' if page else f'{source}.txt')

def numeric(value):
    return float(value) if value not in ('', None) else None
