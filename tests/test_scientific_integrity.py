"""Scientific semantics and byte-for-byte archived-snapshot rebuild checks."""
import csv
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def rows(name):
    with (ROOT/'data'/f'{name}.csv').open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

class ScientificIntegrityTests(unittest.TestCase):
    def test_digestion_wet_and_dry_methane_are_distinct(self):
        methane=[r for r in rows('conversion_parameters') if r['source_id']=='S03' and r['parameter_name']=='Methane production yield']
        self.assertTrue(methane)
        for r in methane:
            self.assertEqual(r['unit'],'m3 CH4/t')
            self.assertTrue('dry metric tonne' in r['measurement_basis'] or 'wet metric tonne' in r['measurement_basis'])
            self.assertNotIn('Nm3',r['unit'])
        self.assertTrue(any('wet' in r['measurement_basis'] for r in methane))
        self.assertTrue(any('dry' in r['measurement_basis'] for r in methane))

    def test_pyrolysis_mass_products_close_in_each_reference_mode(self):
        groups=defaultdict(list)
        for r in rows('conversion_parameters'):
            if r['source_id']=='S07' and r['technology']=='Pyrolysis':
                groups[r['operating_conditions']].append(float(r['value_typical']))
        self.assertEqual(len(groups),3)
        for values in groups.values():
            self.assertEqual(len(values),3)
            self.assertAlmostEqual(sum(values),100)

    def test_source_inconsistencies_are_quarantined(self):
        flagged={r['waste_id'] for r in rows('waste_properties') if r.get('model_ready')=='false'}
        self.assertEqual(len(flagged),2)
        with (ROOT/'data/verified/waste_properties.csv').open(encoding='utf-8') as f:
            allowed={r['waste_id'] for r in csv.DictReader(f)}
        self.assertTrue(flagged.isdisjoint(allowed))

    def test_reference_fuel_and_unsafe_routes_remain_explicit(self):
        for r in rows('technology_performance'):
            if r['electrical_efficiency_pct']:
                self.assertEqual(r['fuel_type'],'natural gas')
                self.assertIn('HHV',r['efficiency_basis'])
        for r in rows('technology_mapping'):
            if r['waste_category']=='Hazardous and medical waste':
                self.assertEqual(r['feasibility_status'],'restricted')
                self.assertEqual(r['hazard_flag'],'true')
                self.assertEqual(r['possible_energy_outputs'],'')
            self.assertNotEqual(r['waste_category'],'Inert waste')

    def test_verified_subset_has_no_orphan_numeric_evidence(self):
        ids=set()
        for name in ['waste_properties','technology_mapping','conversion_parameters','technology_performance']:
            with (ROOT/'data/verified'/f'{name}.csv').open(encoding='utf-8') as f:
                ids.update((name,r['record_id']) for r in csv.DictReader(f))
        with (ROOT/'data/verified/source_verification.csv').open(encoding='utf-8') as f:
            for v in csv.DictReader(f):
                self.assertIn((v['dataset_name'],v['record_id']),ids)

    def test_net_constant_volume_not_silently_labeled_lhv(self):
        historical=[r for r in rows('waste_properties') if r['source_id']=='S01']
        self.assertTrue(any(r['net_heat_constant_volume_mj_kg'] for r in historical))
        self.assertTrue(all(r['lhv_mj_kg']=='' for r in historical))

    def test_offline_rebuild_is_byte_reproducible(self):
        with tempfile.TemporaryDirectory(prefix='wastewise_rebuild_') as temp:
            destination=Path(temp)
            shutil.copytree(ROOT/'scripts',destination/'scripts')
            shutil.copytree(ROOT/'data/raw',destination/'data/raw')
            shutil.copytree(ROOT/'data/processed',destination/'data/processed')
            result=subprocess.run([sys.executable,'-X','utf8',str(destination/'scripts/build_datasets.py')],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(result.returncode,0,result.stderr)
            for name in ['waste_properties','technology_mapping','conversion_parameters','technology_performance','sources','source_verification']:
                self.assertEqual(hashlib.sha256((ROOT/'data'/f'{name}.csv').read_bytes()).hexdigest(),hashlib.sha256((destination/'data'/f'{name}.csv').read_bytes()).hexdigest(),name)

if __name__=='__main__': unittest.main()
