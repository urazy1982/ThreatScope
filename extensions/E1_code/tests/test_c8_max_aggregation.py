"""Regression tests for the v1.1.2 tokenizer diagnostic hotfix. CPU-only."""
import collections
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from c8_prompt_gate import pairwise_token_counts, merge_window_counts
from verify_gpu_authorization import check_c8_hamming_aggregate

class AggregationTests(unittest.TestCase):
    def test_144_windows_single_token_max_is_one(self):
        # 8 variants -> 28 pairs; only one token changes in every comparison.
        variants=[[10, index, 90] for index in range(8)]
        pooled=collections.Counter()
        for _ in range(144):
            merge_window_counts(pooled, pairwise_token_counts(variants))
        self.assertEqual(pooled['pairs'], 4032)
        self.assertEqual(pooled['one'], 4032)
        self.assertEqual(pooled['max_hamming'], 1)
        self.assertEqual(pooled['multi'], 0)

    def test_max_tracks_two_not_sum(self):
        variants=[[0]*9]
        for anchor in range(1,8):
            sample=[0]*9
            sample[anchor]=1
            variants.append(sample)
        pooled=collections.Counter()
        for _ in range(3):
            merge_window_counts(pooled, pairwise_token_counts(variants))
        self.assertEqual(pooled['max_hamming'], 2)
        self.assertEqual(pooled['pairs'], 84)
        self.assertEqual(pooled['multi'], 63)

    def test_launch_gate_rejects_old_maximum_144(self):
        cell={'pairs':4032,'one':4032,'multi':0,'zero':0,'unequal':0,'max_hamming':1}
        summary={'by_instruction':{'B':dict(cell),'C':dict(cell)},
                 'one_token_hamming_pairs':8064,
                 'more_than_one_token_changed_pairs':0,
                 'unequal_length_pairs':0,
                 'max_hamming_distance':1}
        self.assertTrue(check_c8_hamming_aggregate(summary))
        summary['by_instruction']['B']['max_hamming']=144
        summary['max_hamming_distance']=144
        with self.assertRaisesRegex(RuntimeError,'C8_MAX_HAMMING_INCONSISTENT'):
            check_c8_hamming_aggregate(summary)
        summary['by_instruction']['B']['max_hamming']=1
        with self.assertRaisesRegex(RuntimeError,'C8_AGGREGATE_MAXIMUM_MISMATCH'):
            check_c8_hamming_aggregate(summary)

    def test_unequal_length_count_kept_separate(self):
        variants=[[1,i] for i in range(8)]
        variants[7]=[1,7,9]
        result=pairwise_token_counts(variants)
        pooled=merge_window_counts(collections.Counter(),result)
        self.assertEqual(pooled['pairs'],28)
        self.assertEqual(pooled['unequal'],7)
        self.assertEqual(pooled['one'],21)
        self.assertEqual(pooled['max_hamming'],1)
        self.assertEqual(pooled['pairs'],sum(pooled[k] for k in ('unequal','one','multi','zero')))

if __name__=='__main__':
    unittest.main()
