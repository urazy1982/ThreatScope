import unittest,math
from v22core.scoring import candidates,argmax_lowest,softmax,score_candidates_batch,encode_continuations
import torch
from types import SimpleNamespace

class ToyCausalLM(torch.nn.Module):
    def __init__(self,vocab=100):super().__init__();self.vocab=vocab
    def forward(self,input_ids,attention_mask,use_cache=False):
        # For every input position, give token 11 the largest logit.
        B,L=input_ids.shape
        y=torch.zeros(B,L,self.vocab,dtype=torch.float32,device=input_ids.device)
        y[:,:,11]=3
        return SimpleNamespace(logits=y)

class FakeTokenizer:
    unk_token_id=999
    def __init__(self):self.ids={'<|im_end|>':200,'<|eot_id|>':201,'</s>':202}
    def convert_tokens_to_ids(self,x):return self.ids.get(x,self.unk_token_id)
    def encode(self,x,add_special_tokens=False):return list(x.encode('ascii'))
    def decode(self,x,skip_special_tokens=False,clean_up_tokenization_spaces=False):
        if len(x)==1 and x[0] in self.ids.values():return {v:k for k,v in self.ids.items()}[x[0]]
        return bytes(x).decode('ascii')

class ScoringTests(unittest.TestCase):
    def test_8_candidates(self):
        self.assertEqual(len(candidates()),8)
        self.assertEqual(candidates()[3],'{"relevant":[3]}')
    def test_argmax(self):
        r=argmax_lowest([0,0,3,2,3,0,1,3]);self.assertEqual(r['index'],2);self.assertEqual(r['exact_ties'],3)
    def test_invalid_scores(self):
        for xs in ([0]*7,[0]*7+[float('nan')],[0]*7+[float('inf')]):
            with self.subTest(xs=xs),self.assertRaises(ValueError):argmax_lowest(xs)
    def test_softmax(self):
        r=softmax([0]*8);self.assertTrue(all(abs(x-.125)<1e-14 for x in r))
        self.assertAlmostEqual(sum(softmax([3,4,5,6,7,8,9,10])),1)
    def test_stable_softmax(self):self.assertGreater(softmax([1e6]+[0]*7)[0],.999)
    def test_batch_scorer_outputs(self):
        model=ToyCausalLM();ids=torch.tensor([[3,4,5]])
        continuations=[[11,13,14],[13,11,12],[12,13,14],[14,12,11],[11],[11,11],[12,12],[14,14,11]]
        result=score_candidates_batch(model,ids,continuations,pad_token_id=0)
        self.assertEqual(len(result['scores']),8);self.assertEqual(len(result['probability_mass']),8)
        self.assertEqual(result['winner'],4)
    def test_sum_not_length_normalized(self):
        result=score_candidates_batch(ToyCausalLM(),torch.tensor([[1,2,3]]),[[11]]*7+[[11,11]],0)
        self.assertGreater(result['scores'][0],result['scores'][7])
    def test_serial_equivalence(self):
        model=ToyCausalLM(vocab=40);base=torch.tensor([[1,2,3]])
        cc=[[i+4]*((i%3)+1) for i in range(8)]
        batch=score_candidates_batch(model,base,cc,0)
        for i,c in enumerate(cc):
            serial=model(torch.tensor([[1,2,3]+c]),torch.ones(1,3+len(c)),use_cache=False).logits
            values=torch.log_softmax(serial[0,2:2+len(c)].float(),dim=-1)
            target=torch.tensor(c).view(-1,1)
            expected=float(values.gather(1,target).sum())
            self.assertAlmostEqual(batch['scores'][i],expected,places=5)
    def test_shape_reject(self):
        with self.assertRaises(ValueError):score_candidates_batch(ToyCausalLM(),torch.ones(3,dtype=torch.long),[[1]]*8,0)
    def test_bad_continuations(self):
        with self.assertRaises(ValueError):score_candidates_batch(ToyCausalLM(),torch.ones((1,2),dtype=torch.long),[[1]]*7,0)
        with self.assertRaises(ValueError):score_candidates_batch(ToyCausalLM(),torch.ones((1,2),dtype=torch.long),[[]]*8,0)
    def test_tokenizer_end_marker(self):
        from v22core.scoring import END_MARKER
        for model in END_MARKER:
            x=encode_continuations(FakeTokenizer(),model)
            self.assertEqual(len(x),8)
            self.assertEqual(len(x),8)
            self.assertNotEqual(x[0][-1],x[-1][0])
    def test_tokenizer_end_marker_reject(self):
        class Broken(FakeTokenizer):
            def convert_tokens_to_ids(self,x):return self.unk_token_id
        with self.assertRaises(ValueError):encode_continuations(Broken(),'Qwen/Qwen2.5-3B-Instruct')

class SerialScoringRegressionTests(unittest.TestCase):
    def test_exact_serial_batch_equivalence(self):
        from v22core.scoring import score_candidates_serial
        model=ToyCausalLM(vocab=80)
        p=torch.tensor([[1,2,3]])
        c=[[i+4]*(1+i%3) for i in range(8)]
        a=score_candidates_batch(model,p,c,0)
        b=score_candidates_serial(model,p,c)
        for x,y in zip(a['scores'],b['scores']):self.assertAlmostEqual(x,y,places=5)
        self.assertEqual(a['winner'],b['winner'])
    def test_reject_malformed(self):
        from v22core.scoring import score_candidates_serial
        with self.assertRaises(ValueError):score_candidates_serial(ToyCausalLM(),torch.tensor([[1]]),[[4]]*7)
