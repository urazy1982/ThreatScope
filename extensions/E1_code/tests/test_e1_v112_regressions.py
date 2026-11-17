"""CPU-only v1.1.2 methodological regression tests (all synthetic)."""
import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from e1_neutral_gpu import build_prompt, build_messages, SYS, N1_EXAMPLE_LINE, PROTOCOL_ID
from analyze_e1 import disagreement, f1, signflip, validate_labels
from c8_prompt_gate import pairwise_token_counts
from verify_gpu_authorization import verify

class V112Regression(unittest.TestCase):
    def setUp(self):
        self.window={'window_id':'test_window','source':'p','report_id':'r','sentences':[
            {'sentence_text':f'synthetic sentence {i}', 'context_before':'', 'uid':str(i)} for i in range(8)]}

    def test_n1_is_only_append_to_n0(self):
        self.assertEqual(build_prompt(self.window,'N1'),build_prompt(self.window,'N0')+N1_EXAMPLE_LINE)
        self.assertNotIn('OUTPUT FORMAT EXAMPLE',build_prompt(self.window,'N0'))
        self.assertNotIn('"relevant":[0]',build_prompt(self.window,'N1'))

    def test_same_system_instruction_as_historical_core(self):
        with zipfile.ZipFile(ROOT/'upstream/ThreatScope_v1.0.0.zip') as z:
            s=z.read('ThreatScope/src/v221_mechanism/v22core/core.py').decode('utf-8')
        ns={'__name__':'independent_historical_core'}
        exec(compile(s,'historical_core.py','exec'),ns)
        self.assertEqual(SYS,ns['SYS'])
        self.assertTrue(build_prompt(self.window,'N0').startswith(ns['prompt'](self.window,0).split('OUTPUT FORMAT EXAMPLE')[0]))

    def test_all_models_use_same_target_payload(self):
        base=build_prompt(self.window,'N0')
        for model in ['Qwen/Qwen2.5-3B-Instruct','meta-llama/Llama-3.2-3B-Instruct','mistralai/Mistral-7B-Instruct-v0.3']:
            message=' '.join(m['content'] for m in build_messages(model,self.window,'N0'))
            self.assertIn(base,message)
        self.assertEqual(PROTOCOL_ID,'ThreatScope-E1-v1.1.2-minimal-example-intervention')

    def test_pairwise_28_not_7_reference_only(self):
        # Each nonzero anchor differs from anchor zero at one token position;
        # nevertheless, two different nonzero anchors can differ at TWO positions.
        variants=[[0]*9]
        for anchor in range(1,8):
            x=[0]*9;x[anchor]=1;variants.append(x)
        result=pairwise_token_counts(variants)
        self.assertEqual(result['pairs'],28)
        self.assertEqual(result['one'],7)
        self.assertEqual(result['multi'],21)
        self.assertEqual(result['max_hamming'],2)

    def test_disagreement_both_empty(self):
        self.assertEqual(disagreement([],[]),0)
        self.assertEqual(disagreement([0,3],[0,4]),2/8)
        self.assertEqual(disagreement([0,1],[1,0]),0)

    def test_f1_all_positive_missing_penalty(self):
        self.assertEqual(f1(0,0,10),0)
        self.assertEqual(f1(5,0,0),1)
        self.assertEqual(signflip([0]*9),1)

    def test_reject_missing_tokenizer_certificate(self):
        import tempfile
        with tempfile.TemporaryDirectory() as x:
            # The first check is data validation and must reject missing paths,
            # not mistake absent evidence for a certified preflight.
            with self.assertRaises((FileNotFoundError,KeyError,RuntimeError)):
                verify(Path(x)/'no-input',Path(x)/'no-manifest',Path(x),ROOT,'smoke')

if __name__=='__main__':unittest.main()
