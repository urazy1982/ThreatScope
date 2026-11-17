"""Regression for the 2-key BatchEncoding preflight bug."""
import unittest
from unittest.mock import patch
import torch
from crosscti.preflight import count_chat_tokens, run

class FakeTokenizer:
    def __init__(self, n=410): self.n=n
    def apply_chat_template(self, messages, **kw):
        if not kw.get('return_tensors')=='pt':
            return {'input_ids':list(range(self.n)), 'attention_mask':[1]*self.n}
        return torch.zeros((1,self.n),dtype=torch.long)

class FakeDictTokenizer(FakeTokenizer):
    def apply_chat_template(self, *args, **kwargs):
        return {'input_ids':[0]*410,'attention_mask':[1]*410}

class TestPreflight(unittest.TestCase):
    def test_not_batchencoding_len_two(self):
        self.assertEqual(count_chat_tokens(FakeTokenizer(411),[{'role':'user','content':'x'}]),411)
    def test_two_key_batchencoding_counts_actual_ids(self):
        self.assertEqual(count_chat_tokens(FakeDictTokenizer(),[]), 410)
    def test_too_short_cannot_pass(self):
        with self.assertRaisesRegex(RuntimeError,'IMPLAUSIBLY_SHORT'):
            count_chat_tokens(FakeTokenizer(2),[])
    def test_wrong_tensor_shape_fails(self):
        class Bad(FakeTokenizer):
            def apply_chat_template(self,*a,**k):
                return torch.zeros((2,300),dtype=torch.long)
        with self.assertRaisesRegex(RuntimeError,'ENCODING_SHAPE'):
            count_chat_tokens(Bad(),[])
    def test_exact_limit_passes(self):
        self.assertEqual(count_chat_tokens(FakeTokenizer(8192),[]),8192)

if __name__=='__main__':unittest.main()
