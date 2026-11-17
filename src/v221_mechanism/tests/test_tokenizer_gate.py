import unittest
import torch
from v22core.tokenizer_gate import extract_ids,model_messages,continuation_matches_full
from v22core.core import SYS,SYS_SINGLE

class TokenizerPreflightTests(unittest.TestCase):
    def test_2d_tensor(self):self.assertEqual(extract_ids(torch.tensor([[3,7,9]])),[3,7,9])
    def test_two_key_batch_encoding(self):
        x={'input_ids':torch.tensor([[2,4,6]]),'attention_mask':torch.tensor([[1,1,1]])}
        self.assertEqual(extract_ids(x),[2,4,6])
    def test_nested_list(self):self.assertEqual(extract_ids([[1,2,3]]),[1,2,3])
    def test_flat_list(self):self.assertEqual(extract_ids([1,2,3]),[1,2,3])
    def test_unknown_reject(self):
        for x in ([[],[]],{'attention_mask':[]},'invalid',torch.tensor([1,2,3]),torch.tensor([[1],[2]])):
            with self.subTest(x=type(x)),self.assertRaises(RuntimeError):extract_ids(x)
    def test_mistral_user_format(self):
        m=model_messages('mistralai/Mistral-7B-Instruct-v0.3','target',SYS)
        self.assertEqual(len(m),1);self.assertEqual(m[0]['role'],'user')
        self.assertIn('TASK RULES:',m[0]['content'])
    def test_qwen_system_format(self):
        m=model_messages('Qwen/Qwen2.5-3B-Instruct','target',SYS_SINGLE)
        self.assertEqual(len(m),2);self.assertEqual(m[0]['role'],'system')
        self.assertEqual(m[0]['content'],SYS_SINGLE)

class TemplateAlignmentRegressionTests(unittest.TestCase):
    def test_exact_match(self):
        self.assertTrue(continuation_matches_full([7,8],[1,2],[7,8,1,2],[198]))
    def test_qwen_trailing_newline(self):
        self.assertTrue(continuation_matches_full([7,8],[1,2],[7,8,1,2,198],[198]))
    def test_reject_changed_candidate(self):
        self.assertFalse(continuation_matches_full([7,8],[1,2],[7,8,1,3,198],[198]))
    def test_reject_other_suffix(self):
        self.assertFalse(continuation_matches_full([7,8],[1,2],[7,8,1,2,197],[198]))
    def test_reject_multiple_newlines(self):
        self.assertFalse(continuation_matches_full([7,8],[1,2],[7,8,1,2,198,198],[198]))
    def test_reject_empty_suffix_exception(self):
        self.assertFalse(continuation_matches_full([7,8],[1,2],[7,8,1,2,198],[]))
