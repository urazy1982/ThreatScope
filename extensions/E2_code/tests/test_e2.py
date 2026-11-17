import csv,hashlib,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.e2_singleton_gpu import SingletonTrie,check_record,identity_for,normalize_chat_input,PROTOCOL_ID
from scripts.analyze_e2 import signflip
from vendor.v22core.core import SYS_SINGLE,prompt,original_effect
from vendor.e1_neutral_gpu import canonical,sha
from vendor.v22core.tokenizer_gate import extract_ids,continuation_matches_full

class E2Tests(unittest.TestCase):
    def setUp(self):
        self.candidates=[[19,k,99] for k in range(8)]
        self.trie=SingletonTrie(self.candidates)
        self.w={'window_id':'x'*24,'input_sha256':'a'*64,'sentences':[{'context_before':'','sentence_text':f'sentence {j}'} for j in range(8)]}
        self.identity={'protocol':PROTOCOL_ID,'model':'Qwen/Qwen2.5-3B-Instruct','revision':'a'*40,'precision':'bf16'}
    def record(self,idx=2,anchor=1):
        d={'protocol':PROTOCOL_ID,'model':self.identity['model'],'precision':'bf16',
           'revision':self.identity['revision'],'window_id':self.w['window_id'],'anchor':anchor,
           'input_sha256':self.w['input_sha256'],'identity_sha256':sha(canonical(self.identity)),
           'prompt_sha256':'b'*64,'raw':'{"relevant":['+str(idx)+']}',
           'generated_ids':list(self.candidates[idx]),'selected_index':idx,'valid':True}
        d['raw_sha256']=sha(d['raw'])
        d['record_sha256']=sha(canonical(d))
        return d
    def test_canonical_singletons(self):
        self.assertEqual(len(self.trie.candidates),8)
        for idx in range(8):self.assertTrue(self.trie.accepts(self.candidates[idx]))
    def test_prefix_only_valid_ids(self):
        self.assertEqual(self.trie.allowed([]),(19,))
        self.assertEqual(self.trie.allowed([19]),tuple(range(8)))
        self.assertEqual(self.trie.allowed([19,2]),(99,))
        self.assertEqual(self.trie.allowed([19,2,99]),())
    def test_unknown_prefix_fails(self):self.assertFalse(self.trie.allowed([7]))
    def test_duplicate_candidate_rejected(self):
        with self.assertRaises(ValueError):SingletonTrie(self.candidates[:7]+[self.candidates[0]])
    def test_historical_prompts_single_index_mutation(self):
        a,b=prompt(self.w,0),prompt(self.w,7)
        self.assertEqual(len(a),len(b))
        self.assertEqual(sum(x!=y for x,y in zip(a,b)),1)
        self.assertIn('exactly one',SYS_SINGLE)
    def test_original_effect_singleton(self):
        self.assertAlmostEqual(original_effect({i:[i] for i in range(8)})['effect'],1)
        self.assertAlmostEqual(original_effect({i:[0] for i in range(8)})['effect'],0)
    def test_signflip_all_positive(self):self.assertAlmostEqual(signflip([1]*9),2/512)
    def test_checkpoint_valid(self):
        self.assertTrue(check_record(self.record(),self.identity,self.w,1,'b'*64,self.candidates))
    def test_checkpoint_tampered_raw(self):
        r=self.record();r['raw']='{"relevant":[3]}'
        with self.assertRaises(RuntimeError):check_record(r,self.identity,self.w,1,'b'*64,self.candidates)
    def test_checkpoint_wrong_candidate_id(self):
        r=self.record();r['generated_ids']=self.candidates[4];r['record_sha256']=sha(canonical({k:v for k,v in r.items() if k!='record_sha256'}))
        with self.assertRaises(RuntimeError):check_record(r,self.identity,self.w,1,'b'*64,self.candidates)
    def test_checkpoint_wrong_prompt(self):
        with self.assertRaises(RuntimeError):check_record(self.record(),self.identity,self.w,1,'c'*64,self.candidates)
    def test_suffix_alignment_historical_trailing_newline(self):
        prefix=[1,2,3];candidate=[4,5,6];newline=[7]
        self.assertTrue(continuation_matches_full(prefix,candidate,prefix+candidate,newline))
        self.assertTrue(continuation_matches_full(prefix,candidate,prefix+candidate+newline,newline))
        self.assertFalse(continuation_matches_full(prefix,candidate,prefix+candidate+[9],newline))
        self.assertFalse(continuation_matches_full(prefix,candidate,prefix+[4,8,6]+newline,newline))
    def test_chat_token_id_normalization(self):
        self.assertEqual(extract_ids([1,2,3]),[1,2,3])
        self.assertEqual(extract_ids([[1,2,3]]),[1,2,3])
        self.assertEqual(extract_ids({'input_ids':[1,2,3]}),[1,2,3])
    def test_chat_input_normalizes_flat_list(self):
        import torch
        x=normalize_chat_input([1,2,3],torch,expected_ids=[1,2,3])
        self.assertEqual(tuple(x.shape),(1,3))
        self.assertEqual(x.dtype,torch.long)
        self.assertEqual(x.tolist(),[[1,2,3]])
    def test_chat_input_normalizes_dictionary(self):
        import torch
        self.assertEqual(normalize_chat_input({'input_ids':[[1,2,3]]},torch).tolist(),[[1,2,3]])
    def test_chat_input_normalizes_tensor(self):
        import torch
        self.assertEqual(normalize_chat_input(torch.tensor([[1,2,3]]),torch).tolist(),[[1,2,3]])
    def test_chat_input_rejects_wrong_batch(self):
        import torch
        with self.assertRaises(RuntimeError):
            normalize_chat_input(torch.tensor([[1,2],[3,4]]),torch)
    def test_chat_input_rejects_token_drift(self):
        import torch
        with self.assertRaisesRegex(RuntimeError,'CHAT_INPUT_TOKEN_DRIFT'):
            normalize_chat_input([1,2,3],torch,expected_ids=[1,2,4])
    def test_chat_input_rejects_empty(self):
        import torch
        with self.assertRaises(RuntimeError):normalize_chat_input([],torch)
    def test_archived_armC_reference_counts(self):
        with (ROOT/'reference/archived_armC_6912_winners.csv').open() as f:r=list(csv.DictReader(f))
        self.assertEqual(len(r),6912)
        self.assertEqual(len({(x['model'],x['precision'],x['window_id'],int(x['anchor'])) for x in r}),6912)
        self.assertEqual(len({x['window_id'] for x in r}),144)
    def test_archived_reference_sha(self):
        prov=json.loads((ROOT/'reference/ARCHIVED_ARM_C_PROVENANCE.json').read_text())
        self.assertEqual(prov['archived_checkpoint_record_hashes_checked'],6912)
        self.assertEqual(hashlib.sha256((ROOT/'reference/archived_armC_6912_winners.csv').read_bytes()).hexdigest(),prov['winners_csv_sha256'])
if __name__=='__main__':unittest.main()
