import unittest
from pathlib import Path
from v22core.evidence_audit import audit
from v22core.null import simulate
ROOT=Path(__file__).resolve().parents[1]

class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=audit(ROOT/'reference/ThreatStudy_v216_Complete_Results.zip',
            ROOT/'evidence/APT_final_cpu_gate_v215.json',ROOT/'evidence/APT_preflight_v214.json')
    def test_status(self):self.assertEqual(self.result['status'],'REFERENCE_PROVENANCE_AND_TOKEN_COUNTS_PASS')
    def test_all_tokens_match(self):
        for r in self.result['models']:
            self.assertEqual(r['actual_archived_max_input_tokens'],r['preflight_report_max_input_tokens'])
    def test_prompt_equality(self):
        for r in self.result['models']:self.assertEqual(r['prompt_token_length_disagreements'],0)
    def test_generation_duration_nonzero(self):
        for r in self.result['models']:
            for p in r['precisions'].values():self.assertGreater(p['sum_latency_seconds'],0)

class NullTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=simulate(ROOT/'reference/ThreatStudy_v216_Complete_Results.zip',draws=200,seed=999)
    def test_all_models(self):self.assertEqual(len(self.sim['models']),3)
    def test_cardinality_null_centered(self):
        for r in self.sim['models']:self.assertLess(abs(r['null_mean']),.01)
    def test_reproducible(self):
        again=simulate(ROOT/'reference/ThreatStudy_v216_Complete_Results.zip',draws=200,seed=999)
        self.assertEqual(self.sim,again)
    def test_no_confirmatory_claim(self):
        self.assertIn('not a randomized experiment',self.sim['models'][0]['interpretation'])
