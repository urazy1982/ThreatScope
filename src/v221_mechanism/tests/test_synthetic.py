import unittest,copy
from pathlib import Path
from v22core.replay import validate_archive
from v22core.synthetic import generated_records,evaluate,verify_record
R=Path(__file__).resolve().parents[1]
class SyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.m,cls.windows,_,_=validate_archive(R/'reference/ThreatStudy_v216_Complete_Results.zip')
        cls.rows=list(generated_records(cls.windows,cls.cfg['models'],cls.cfg,cls.m))
        cls.result=evaluate(cls.rows,cls.windows,cls.cfg,cls.m)
    def test_count(self):self.assertEqual(len(self.rows),13824)
    def test_models_arms(self):self.assertEqual(len(self.result['model_results']),6)
    def test_synthetic_strong_effect(self):
        for r in self.result['model_results']:
            self.assertGreater(r['synthetic_interaction'],.3)
            self.assertLessEqual(r['synthetic_holm_p'],.05)
    def test_c_probability_vector(self):
        for r in self.rows:
            if r['arm']=='C_single_choice':self.assertAlmostEqual(sum(r['candidate_softmax']),1)
    def test_b_valid(self):
        for r in self.rows:
            if r['arm']=='B_schema':self.assertTrue(r['valid'])
    def test_tamper(self):
        row=copy.deepcopy(self.rows[0]);row['indices']=[7]
        with self.assertRaises(RuntimeError):verify_record(row,self.windows[0],self.cfg,self.m)
    def test_missing(self):
        with self.assertRaises(RuntimeError):evaluate(self.rows[:-1],self.windows,self.cfg,self.m)
    def test_duplicate(self):
        with self.assertRaises(RuntimeError):evaluate(self.rows+[self.rows[0]],self.windows,self.cfg,self.m)
