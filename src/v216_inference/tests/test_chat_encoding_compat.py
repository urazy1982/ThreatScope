import unittest
import torch
from crosscti.token_encoding import chat_input_ids
from crosscti.preflight import count_chat_tokens

class MockBatchEncoding(dict):
    pass
class MockTokenizer:
    def __init__(self, output): self.output=output
    def apply_chat_template(self,*args,**kwargs): return self.output

class TestChatEncodingCompatibility(unittest.TestCase):
    def test_tensor(self):
        x=torch.arange(280).reshape(1,280)
        self.assertTrue(torch.equal(chat_input_ids(x),x))
    def test_batch_encoding_tensor(self):
        x=torch.arange(280).reshape(1,280)
        obj=MockBatchEncoding(input_ids=x,attention_mask=torch.ones_like(x))
        self.assertTrue(torch.equal(chat_input_ids(obj),x))
        self.assertEqual(count_chat_tokens(MockTokenizer(obj),[]),280)
    def test_batch_encoding_list(self):
        obj=MockBatchEncoding(input_ids=[[i for i in range(350)]],attention_mask=[[1]*350])
        self.assertEqual(chat_input_ids(obj).shape,(1,350))
    def test_flat_list(self):
        self.assertEqual(chat_input_ids({'input_ids':[1,2,3]}).shape,(1,3))
    def test_missing_ids(self):
        with self.assertRaisesRegex(RuntimeError,'MISSING_INPUT_IDS'): chat_input_ids({'attention_mask':[]})
    def test_unbatched_tensor(self):
        self.assertEqual(chat_input_ids(torch.tensor([1,2,3])).shape,(1,3))
    def test_two_batches_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'CHAT_ENCODING_SHAPE'): chat_input_ids(torch.ones((2,4),dtype=torch.long))
    def test_bad_rank_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'CHAT_ENCODING_SHAPE'): chat_input_ids(torch.ones((1,2,3),dtype=torch.long))
    def test_negative_ids_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'NEGATIVE_ID'):chat_input_ids(torch.tensor([[2,-1]]))
    def test_string_ids_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'NOT_NUMERIC'):chat_input_ids({'input_ids':[['x']]})
    def test_float_ids_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'NOT_INTEGER'):chat_input_ids({'input_ids':[[1.5,2.5]]})
    def test_empty_ids_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'CHAT_ENCODING_SHAPE'):chat_input_ids({'input_ids':[]})

if __name__=='__main__':unittest.main()
