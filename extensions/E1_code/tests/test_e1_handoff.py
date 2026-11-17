"""Synthetic-only unit checks: never evidence of real model inference."""
import sys,unittest,subprocess,tempfile,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_gpu_idle import check
from analyze_e1 import f1,signflip
from e1_neutral_gpu import SYS,canonical,sha,build_prompt,build_messages,parse_output
from audit_e1 import verify_cell

class TestHandoff(unittest.TestCase):
 def test_busy_gpu_denied(self):
  r=subprocess.CompletedProcess(['nvidia-smi'],0,stdout='6013\n',stderr='')
  with self.assertRaisesRegex(RuntimeError,'GPU_BUSY_COMPUTE_PIDS=6013'):
   check(r)
 def test_gpu_query_failure_denied(self):
  r=subprocess.CompletedProcess(['nvidia-smi'],1,stdout='',stderr='not accessible')
  with self.assertRaisesRegex(RuntimeError,'GPU_QUERY_FAILED'):
   check(r)
 def test_idle_gpu_accepted(self):
  r=subprocess.CompletedProcess(['nvidia-smi'],0,stdout='\n',stderr='');self.assertTrue(check(r))
 def test_signflip_9_pub_and_f1(self):
  self.assertAlmostEqual(signflip([1]*9),2/512)
  self.assertEqual(f1(0,0,3),0.)
  self.assertAlmostEqual(f1(2,1,1),4/6)
 def test_invalid_predictions_rejected(self):
  self.assertFalse(parse_output('{"relevant":[true]}')[0]);self.assertFalse(parse_output('{"relevant":[9]}')[0])
 def test_checkpoint_tampering_detected(self):
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);root=Path(__file__).resolve().parents[1]
   model='Qwen/Qwen2.5-3B-Instruct';p='bf16';condition='N0';rev='rev_mock_01'
   windows=[]
   for i in range(2):
    w={'window_id':f'w{i}','input_sha256':f'fp{i}',
       'sentences':[{'context_before':'','sentence_text':f'fake target {k}'} for k in range(8)]}
    windows.append(w)
   manifest={'input_sha256':'frozen_mock_hash'};cfg={'models':{model:rev},'max_new_tokens':96}
   identity=dict(protocol='ThreatScope-E1-v1.1.2-minimal-example-intervention',model=model,revision=rev,precision=p,condition=condition,
    inputs_sha256=manifest['input_sha256'],sys_sha256=sha(SYS),code_sha256=hashlib.sha256((root/'scripts/e1_neutral_gpu.py').read_bytes()).hexdigest(),
    generation={'do_sample':False,'num_beams':1,'max_new_tokens':96,'pad_token_id':'eos'},additional_dependencies={},
    torch='torch',transformers='transformers',bitsandbytes='bnb')
   (d/'identity.json').write_text(json.dumps(identity));(d/'load_provenance.json').write_text(json.dumps(dict(model=model,revision=rev,precision=p,verified_4bit_linear_modules=0,tokenizer_chat_template_sha256='sha',cuda_device='GPU',pytorch='torch',transformers='transformers',bitsandbytes='bnb',additional_dependencies={})))
   for w in windows:
    msgs=build_messages(model,w,condition)
    raw='{"relevant":[0]}'
    rec={'window_id':w['window_id'],'input_sha256':w['input_sha256'],'identity':sha(canonical(identity)),
     'prompt_sha256':sha(canonical(msgs)),'raw':raw,'raw_sha256':sha(raw),'indices':[0],'valid':True,'error':'ok',
     'prompt_tokens':100,'generated_tokens':10,'generation_cap_reached':False}
    rec['record_sha256']=sha(canonical(rec));(d/(w['window_id']+'.json')).write_text(json.dumps(rec))
   (d/'cell_status.json').write_text(json.dumps(dict(model=model,precision=p,condition=condition,requested_windows=2,completed_windows=2,valid_windows=2,invalid_windows=0,complete_full_cell=False,identity=sha(canonical(identity)))))
   self.assertEqual(verify_cell(d,model,p,condition,windows,manifest,cfg,2)['valid'],2)
   prov=d/'load_provenance.json';original_prov=prov.read_text()
   drift=json.loads(original_prov);drift['additional_dependencies']={'huggingface-hub':'tampered'}
   prov.write_text(json.dumps(drift))
   with self.assertRaisesRegex(RuntimeError,'RUNTIME_DEPENDENCY_DRIFT'):
    verify_cell(d,model,p,condition,windows,manifest,cfg,2)
   prov.write_text(original_prov)
   path=d/'w0.json';tampered=json.loads(path.read_text());tampered['indices']=[1];path.write_text(json.dumps(tampered))
   with self.assertRaisesRegex(RuntimeError,'CHECKPOINT_CONTENT_DRIFT|PARSER_REPLAY_MISMATCH'):
    verify_cell(d,model,p,condition,windows,manifest,cfg,2)

if __name__=='__main__':unittest.main()
