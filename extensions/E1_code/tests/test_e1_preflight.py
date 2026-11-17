"""Fully synthetic DATA-GATE unit tests; never mistaken for empirical results."""
import sys,unittest,json,hashlib,tempfile,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from e1_neutral_gpu import verify_frozen_inputs,canonical,sha,build_prompt,parse_output

class TestFrozenPreflight(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);(self.root/'config').mkdir();(self.root/'outputs/prepared').mkdir(parents=True)
  self.conf=self.root/'config/study.json';self.inputs=self.root/'outputs/prepared/inputs.jsonl';self.manifest=self.root/'outputs/prepared/manifest.json'
  self.cfg={'protocol':'synthetic-only','precisions':['bf16','nf4'],'models':{'Synthetic/Model':'synthetic_sha'}}
  self.conf.write_text(json.dumps(self.cfg))
  self.ws=[]
  for pi in range(9):
   for ri in range(8):
    for slot in range(2):
     w={'source':f'pub{pi}','report_id':f'r{pi}_{ri}','window_id':f'w{pi}_{ri}_{slot}','window_slot':slot,
         'sentences':[{'uid':f'u{pi}_{ri}_{slot}_{k}','sentence_text':f'Synthetic target {pi}-{ri}-{slot}-{k}','context_before':''} for k in range(8)]}
     w['input_sha256']=sha(canonical(w));self.ws.append(w)
  self.dump()
 def dump(self):
  raw=(''.join(canonical(w)+'\n' for w in self.ws)).encode();self.inputs.write_bytes(raw)
  cfg_raw=self.conf.read_bytes();self.manifest.write_text(json.dumps({'windows':144,'input_sha256':hashlib.sha256(raw).hexdigest(),
      'config_sha256':hashlib.sha256(cfg_raw).hexdigest(),'protocol':'synthetic-only'}))
 def test_valid_int_manifest(self):
  m,windows,c=verify_frozen_inputs(self.inputs,self.manifest,'Synthetic/Model');self.assertEqual(m['windows'],144);self.assertEqual(len(windows),144)
 def test_tampered_file_hash_rejected(self):
  self.inputs.write_bytes(self.inputs.read_bytes()+b' ')
  with self.assertRaisesRegex(RuntimeError,'FROZEN_INPUT_HASH_MISMATCH'):verify_frozen_inputs(self.inputs,self.manifest)
 def test_config_hash_rejected(self):
  self.conf.write_text(self.conf.read_text()+' ')
  with self.assertRaisesRegex(RuntimeError,'FROZEN_CONFIG_NOT_UNIQUELY_RESOLVED'):verify_frozen_inputs(self.inputs,self.manifest)
 def test_duplicate_window_id_rejected(self):
  self.ws[1]['window_id']=self.ws[0]['window_id'];self.ws[1]['input_sha256']=sha(canonical({k:v for k,v in self.ws[1].items() if k!='input_sha256'}));self.dump()
  with self.assertRaisesRegex(RuntimeError,'DUPLICATE_WINDOW_ID'):verify_frozen_inputs(self.inputs,self.manifest)
 def test_blank_target_rejected(self):
  self.ws[1]['sentences'][0]['sentence_text']='';self.ws[1]['input_sha256']=sha(canonical({k:v for k,v in self.ws[1].items() if k!='input_sha256'}));self.dump()
  with self.assertRaisesRegex(RuntimeError,'MISSING_OR_REDACTED_SOURCE_TEXT'):verify_frozen_inputs(self.inputs,self.manifest)
 def test_unknown_model_rejected(self):
  with self.assertRaisesRegex(RuntimeError,'MODEL_NOT_IN_FROZEN_CONFIG'):verify_frozen_inputs(self.inputs,self.manifest,'other')
 def test_neutral_templates_and_schema(self):
  for c in ('N0','N1'):
   p=build_prompt(self.ws[0],c)
   self.assertIn('TARGET_SENTENCES_JSON',p)
   self.assertNotIn('{"relevant":[0]}',p)
   if c=='N0':self.assertNotIn('OUTPUT FORMAT EXAMPLE',p)
   else:self.assertIn('OUTPUT FORMAT EXAMPLE',p);self.assertIn('{"relevant":[]}',p)
  self.assertEqual(parse_output('{"relevant":[0,2]}'),(True,[0,2],'ok'))
  self.assertFalse(parse_output('{"relevant":[0,0]}')[0])

if __name__=='__main__':unittest.main()
