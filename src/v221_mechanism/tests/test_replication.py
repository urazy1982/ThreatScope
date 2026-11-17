from pathlib import Path
import unittest
from v22core.replication import build,compare

Z=Path(__file__).resolve().parents[1]/'reference/ThreatStudy_v216_Complete_Results.zip'

class ReplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=build(Z)
    def test_length(self):self.assertEqual(cls_len:=self.data['n_calls'],432)
    def test_one_window_per_publisher(self):
        self.assertEqual(len({x['publisher'] for x in self.data['selected_windows']}),9)
        self.assertEqual(len({x['window_id'] for x in self.data['selected_windows']}),9)
    def test_full_key_set(self):
        keys={(c['model'],c['precision'],c['window_id'],c['anchor']) for c in self.data['calls']}
        self.assertEqual(len(keys),432)
    def test_reproducible(self):self.assertEqual(self.data,build(Z))
    def test_compare_matching(self):
        x=[]
        for c in self.data['calls']:
            x.append({'model':c['model'],'revision':c['model_revision'],'precision':c['precision'],
            'window_id':c['window_id'],'anchor':c['anchor'],'raw_sha256':c['archived_raw_sha256'],
            'indices':c['archived_indices'],'valid':c['archived_valid']})
        d=compare(self.data,x)
        self.assertEqual(d['counts']['byte_exact'],432)
        self.assertTrue(d['arm_A_reuse_for_direct_within_environment_comparison'])
    def test_compare_mismatch(self):
        x=[]
        for c in self.data['calls']:
            x.append({'model':c['model'],'revision':c['model_revision'],'precision':c['precision'],
            'window_id':c['window_id'],'anchor':c['anchor'],'raw_sha256':c['archived_raw_sha256'],
            'indices':c['archived_indices'],'valid':c['archived_valid']})
        x[0]['raw_sha256']='tampered'
        d=compare(self.data,x)
        self.assertEqual(d['counts']['byte_exact'],431)
        self.assertFalse(d['arm_A_reuse_for_direct_within_environment_comparison'])
    def test_mismatched_revision(self):
        x=[]
        for c in self.data['calls']:
            x.append({'model':c['model'],'revision':c['model_revision'],'precision':c['precision'],
            'window_id':c['window_id'],'anchor':c['anchor'],'raw_sha256':c['archived_raw_sha256'],
            'indices':c['archived_indices'],'valid':c['archived_valid']})
        x[-1]['revision']='unfrozen'
        with self.assertRaises(RuntimeError):compare(self.data,x)
