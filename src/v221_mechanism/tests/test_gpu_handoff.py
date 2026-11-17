import copy,math,unittest
from v22core.gpu_handoff import validate_gate,verify_rec,rec_hash,EXPECTED_INPUT,EXPECTED_DATASET
from v22core.core import digest,SYS_SINGLE,prompt

CFG={'models':{'Qwen/Qwen2.5-3B-Instruct':'q', 'meta-llama/Llama-3.2-3B-Instruct':'l',
    'mistralai/Mistral-7B-Instruct-v0.3':'m'}}
M={'dataset_sha256':EXPECTED_DATASET,'input_sha256':EXPECTED_INPUT}

def good_gate():
    return {'status':'V22_REAL_CPU_TOKENIZER_PREFLIGHT_PASS',
     'dataset_sha256':EXPECTED_DATASET,'input_sha256':EXPECTED_INPUT,
     'models':[{'model':n,'revision':r,'status':'PASS','unequal_B':0,'unequal_C':0,
       'full_template_alignment_errors':0,'candidate_token_lengths':[6]*8,
       'max_tokens_B':1200,'max_tokens_C':1230,
       'B_canonical_token_trie':{'canonical_outputs':256}} for n,r in CFG['models'].items()]}

class DataBoundGateTests(unittest.TestCase):
    def test_positive_synthetic_gate(self):self.assertTrue(validate_gate(good_gate(),CFG,M))
    def test_missing_revision(self):
        g=good_gate();g['models'][0]['revision']='wrong'
        with self.assertRaises(RuntimeError):validate_gate(g,CFG,M)
    def test_missing_canonical_subsets(self):
        g=good_gate();g['models'][1]['B_canonical_token_trie']['canonical_outputs']=255
        with self.assertRaises(RuntimeError):validate_gate(g,CFG,M)
    def test_prompt_mismatch_rejected(self):
        g=good_gate();g['models'][2]['full_template_alignment_errors']=1
        with self.assertRaises(RuntimeError):validate_gate(g,CFG,M)
    def test_unbalanced_candidates_rejected(self):
        g=good_gate();g['models'][0]['candidate_token_lengths'][-1]=7
        with self.assertRaises(RuntimeError):validate_gate(g,CFG,M)
    def test_dataset_hash_changed(self):
        g=good_gate();g['input_sha256']='bad'
        with self.assertRaises(RuntimeError):validate_gate(g,CFG,M)
    def test_failing_status(self):
        g=good_gate();g['status']='FAKE_PASS'
        with self.assertRaises(RuntimeError):validate_gate(g,CFG,M)

class CheckpointIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.window={'window_id':'w','input_sha256':'h','sentences':[{'context_before':'','sentence_text':'test'}]*8}
        self.identity={'model_revision':'r'}
        self.reco={'arm':'C','model':'m','precision':'nf4','anchor':1,
            'window_id':'w','input_sha256':'h','revision':'r',
            'identity_sha256':digest(self.identity),'prompt_sha256':digest([SYS_SINGLE,prompt(self.window,1),'m']),'indices':[0],'valid':True,
            'scores':[2.,1.,0.,0.,0.,0.,0.,0.],
            'probability_mass':__import__('v22core.scoring',fromlist=['softmax']).softmax([2.,1.,0.,0.,0.,0.,0.,0.]),
            'exact_ties':1}
        self.reco['record_sha256']=rec_hash(self.reco)
    def verify(self,r):return verify_rec(r,self.identity,self.window,1,'m','nf4','C')
    def test_valid_score_record(self):self.verify(self.reco)
    def test_tampered_hash_rejected(self):
        x=copy.deepcopy(self.reco);x['scores'][0]+=1
        with self.assertRaises(RuntimeError):self.verify(x)
    def test_invalid_winner_rejected(self):
        x=copy.deepcopy(self.reco);x['indices']=[3];x['record_sha256']=rec_hash(x)
        with self.assertRaises(RuntimeError):self.verify(x)
    def test_non_finite_rejected(self):
        x=copy.deepcopy(self.reco);x['scores'][0]=float('nan');x['record_sha256']=rec_hash(x)
        with self.assertRaises(RuntimeError):self.verify(x)
    def test_invalid_prob_mass_rejected(self):
        x=copy.deepcopy(self.reco);x['probability_mass'][0]=0;x['record_sha256']=rec_hash(x)
        with self.assertRaises(RuntimeError):self.verify(x)
    def test_ident_changed_rejected(self):
        x=copy.deepcopy(self.reco);x['identity_sha256']='wrong';x['record_sha256']=rec_hash(x)
        with self.assertRaises(RuntimeError):self.verify(x)
