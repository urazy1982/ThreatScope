import unittest,sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vendor.core import prompt,parse
from scripts.e4_runner import PROTOCOL,checkpoint_expected,load_frozen
from scripts.audit_e4 import D,MODELS
class E4(unittest.TestCase):
 def setUp(self):self.w={'window_id':'w','input_sha256':'h','sentences':[{'sentence_text':f'Target {i}','context_before':''} for i in range(8)]}
 def test_protocol(self):self.assertIn('E4-FP4',PROTOCOL)
 def test_config_protocol_binding(self):
  cfg=json.loads((Path(__file__).resolve().parents[1]/'reference_config.json').read_text())
  self.assertEqual(cfg['e4_protocol'],PROTOCOL)
  self.assertEqual(cfg['max_new_tokens'],96)
  self.assertEqual(cfg['max_input_tokens'],8192)
 def test_prompts(self):
  for k in range(8):self.assertIn('{"relevant":['+str(k)+']}',prompt(self.w,k))
 def test_parser(self):self.assertEqual(parse('{"relevant":[1,3]}')['indices'],[1,3])
 def test_bad_json(self):self.assertFalse(parse('not-json')['valid'])
 def test_zero_dependence(self):self.assertEqual(D({k:{'valid':True,'indices':[0]} for k in range(8)}),0)
 def test_positive_dependence(self):self.assertEqual(D({k:{'valid':True,'indices':[k]} for k in range(8)}),1)
 def test_invalid_as_empty(self):self.assertEqual(D({k:{'valid':False,'indices':[]} for k in range(8)}),0)
 def test_model_count(self):self.assertEqual(len(MODELS),2)
 def test_hash_binding(self):self.assertEqual(checkpoint_expected(self.w,0,'Qwen/Qwen2.5-3B-Instruct','fp4','rev','id')['precision'],'fp4')
if __name__=='__main__':unittest.main()
