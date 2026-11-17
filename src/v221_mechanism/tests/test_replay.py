import unittest,math,json
from pathlib import Path
from v22core.replay import validate_archive,compute
from v22core.null import simulate
Z=Path(__file__).resolve().parents[1]/'reference/ThreatStudy_v216_Complete_Results.zip'

class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.m,cls.windows,cls.rows,cls.audit=validate_archive(Z)
        cls.res,cls.per,cls.src,cls.ix=compute(cls.cfg,cls.m,cls.windows,cls.rows)
    def test_full_records_verified(self):self.assertEqual(self.audit['checkpoints_verified'],6912)
    def test_environment_count(self):self.assertEqual(self.audit['environment_cells_verified'],6)
    def test_invalid_count(self):self.assertEqual(self.audit['invalid_outputs'],87)
    def test_dataset(self):self.assertEqual(self.m['dataset_sha256'],'461682f329a5cca95715d6d7a12356dddb3f38f3adf0e221a2443bdecfdd354e')
    def test_rows(self):self.assertEqual(len(self.per),432)
    def test_per_index_rows(self):self.assertEqual(len(self.ix),6912)
    def test_source_rows(self):self.assertEqual(len(self.src),27)
    def test_source_equal(self):self.assertTrue(all(x['reports']==8 for x in self.src))
    def test_raw_recompute(self):
        known={'Qwen/Qwen2.5-3B-Instruct':.11359126984126984,
         'meta-llama/Llama-3.2-3B-Instruct':.049727182539682536,
         'mistralai/Mistral-7B-Instruct-v0.3':.060143849206349215}
        for x in self.res['models']:self.assertAlmostEqual(x['raw_delta'],known[x['model']])
    def test_all_cardinality_decomposition(self):
        for row in self.per:self.assertAlmostEqual(row['raw_interaction'],row['diagonal_contribution']+row['cardinality_contribution'])
    def test_mass_exploratory_values(self):
        known={'Qwen/Qwen2.5-3B-Instruct':.09731434240362812,
         'meta-llama/Llama-3.2-3B-Instruct':.016604072184429323,
         'mistralai/Mistral-7B-Instruct-v0.3':.020301870748299325}
        for x in self.res['models']:self.assertAlmostEqual(x['mass_normalized_delta_exploratory'],known[x['model']])
    def test_holm(self):self.assertEqual(sorted(x['raw_holm'] for x in self.res['models']),[.01171875,.015625,.015625])
    def test_qwen_copy(self):
        q=next(x for x in self.res['models'] if x['model'].startswith('Qwen/'))
        self.assertEqual((q['bf16_singleton_copy'],q['nf4_singleton_copy']),(15,119))
    def test_qwen_invalidity(self):
        q=next(x for x in self.res['models'] if x['model'].startswith('Qwen/'))
        self.assertEqual((q['bf16_invalid'],q['nf4_invalid']),(69,5))
    def test_lama_diagonal_reduction(self):
        x=next(x for x in self.res['models'] if x['model'].startswith('meta-llama/'))
        self.assertLess(x['raw_diagonal_contribution'],0)
        self.assertGreater(x['raw_cardinality_contribution'],0)
    def test_all_leave_one_source_out(self):
        for x in self.res['models']:self.assertGreater(x['leave_one_publisher_out_raw_range'][0],0)
    def test_mass_holm(self):self.assertEqual(sorted(x['mass_holm_exploratory'] for x in self.res['models']),[.01171875,.015625,.015625])
    def test_no_gold(self):self.assertTrue(self.m['dataset_sha256'] and self.cfg['no_gold_labels'])
