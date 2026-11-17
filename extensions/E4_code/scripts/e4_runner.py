#!/usr/bin/env python3
"""Frozen historical Arm A prompt, E3 holdout: checkpoint-verified inference."""
import argparse,hashlib,json,sys,time,gc,os,random,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vendor.core import SYS,prompt,parse,digest,read,write,lines
from vendor.token_encoding import chat_input_ids

PROTOCOL='ThreatScope-E4-FP4-v0.1-historical-ArmA-interior-report-holdout'
INPUT_SHA='84c02a30c6f077d1c2d0e645be480616e66d93dd61ca5d660acb77bed37216b3'
HIST_INPUT_SHA='e22310e37efe29c2f29f8ec51b931d765a371cc9f7628b52337fa86ce338500b'
EXPECTED={'securelist_apt':10,'trendmicro_apt':10,'unit42_apt':9,'talos_apt':9,'groupib_apt':7,'volexity_apt':9,'sentinellabs_apt':9,'asec_apt':9}

def sha_file(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def load_frozen(input_path,gate_path,config_path):
 from collections import Counter
 assert sha_file(input_path)==INPUT_SHA,'FROZEN_INPUT_SHA_MISMATCH'
 gate=read(gate_path);cfg=read(config_path)
 assert gate['status']=='PASS' and gate['new_inputs_sha256']==INPUT_SHA,'E3_GATE_INVALID'
 assert gate['frozen_old_inputs_sha256']==HIST_INPUT_SHA,'HISTORICAL_INPUT_IDENTITY_MISMATCH'
 assert gate['counts_by_publisher']==EXPECTED,'PUBLISHER_ALLOCATION_MISMATCH'
 assert gate['protocol']=='ThreatScope-E3-v0.3-interior-report-holdout-8-publisher','E3_GATE_PROTOCOL_MISMATCH'
 assert cfg['max_new_tokens']==96 and cfg['max_input_tokens']==8192 and cfg['e4_protocol']==PROTOCOL,'DECODE_CONFIG_DRIFT'
 assert cfg['anchor_indices']==list(range(8)),'EXAMPLE_INDICES_DRIFT'
 ws=lines(input_path)
 assert len(ws)==72 and len({w['window_id'] for w in ws})==72 and len({w['report_id'] for w in ws})==72,'WINDOW_REPORT_COUNT_DRIFT'
 assert dict(Counter(w['source'] for w in ws))==EXPECTED,'WINDOW_PUBLISHER_MISMATCH'
 assert all(len(w['sentences'])==8 for w in ws),'WINDOW_TARGET_COUNT_DRIFT'
 assert all(all(isinstance(s.get('sentence_text'),str) and s['sentence_text'].strip() and isinstance(s.get('context_before'),str) for s in w['sentences']) for w in ws),'BAD_TARGET_TEXT'
 return ws,gate,cfg

def model_messages(model,text):
 if model.startswith('mistralai/'):
  return [{'role':'user','content':'TASK RULES:\n'+SYS+'\n\nUNTRUSTED TARGET INPUT:\n'+text}]
 return [{'role':'system','content':SYS},{'role':'user','content':text}]

def checkpoint_expected(w,k,model,precision,revision,identity_sha):
 return {'window_id':w['window_id'],'input_sha256':w['input_sha256'],'anchor':k,'model':model,'precision':precision,'revision':revision,'identity_sha256':identity_sha,'prompt_sha256':digest([SYS,prompt(w,k),model])}

def validate_checkpoint(p,w,k,model,precision,revision,identity_sha):
 r=read(p)
 for key,val in checkpoint_expected(w,k,model,precision,revision,identity_sha).items():
  if r.get(key)!=val:raise RuntimeError('CHECKPOINT_DRIFT '+str(p)+' '+key)
 if r.get('raw_sha256')!=digest(r.get('raw','')):raise RuntimeError('RAW_DRIFT '+str(p))
 if r.get('record_sha256')!=digest({a:b for a,b in r.items() if a!='record_sha256'}):raise RuntimeError('RECORD_DRIFT '+str(p))
 x=parse(r['raw'])
 if (r['valid'],r['indices'],r['error'])!=(x['valid'],x['indices'],x['error']):raise RuntimeError('PARSER_DRIFT '+str(p))
 return r

def idle():
 p=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],capture_output=True,text=True)
 if p.returncode:raise RuntimeError('NVIDIA_SMI_FAILED '+p.stderr)
 x=[a.strip() for a in p.stdout.splitlines() if a.strip() and a.strip().lower() not in ('no running processes found','[not supported]')]
 if x:raise RuntimeError('GPU_BUSY '+str(x))

def run(args):
 ws,gate,cfg=load_frozen(Path(args.inputs),Path(args.gate),Path(args.config))
 assert args.model in cfg['models'] and args.precision=='fp4' and cfg['precisions']==['fp4'],'MODEL_PRECISION_DRIFT'
 revision=cfg['models'][args.model]
 base=Path(args.out);base.mkdir(parents=True,exist_ok=True)
 identity={'protocol':PROTOCOL,'gate_sha256':sha_file(args.gate),'input_sha256':INPUT_SHA,'model':args.model,'revision':revision,'precision':args.precision,'prompt_definition_sha256':sha_file(Path(__file__).resolve().parents[1]/'vendor/core.py'),'max_new_tokens':96,'seed':cfg['seed'],'runner_sha256':sha_file(__file__),'stack_versions':{'torch':'2.10.0+cu128','transformers':'5.22.2','bitsandbytes':'0.50.2'}}
 ih=digest(identity);meta=base/'run_metadata.json'
 if meta.exists() and read(meta)!=identity:raise RuntimeError('METADATA_DRIFT')
 subset=ws[:args.limit] if args.limit else ws
 n=len(subset)*8;done=0
 for w in subset:
  for k in range(8):
   f=base/f'example_{k}'/(w['window_id']+'.json')
   if f.exists():
    if not meta.exists():raise RuntimeError('ORPHAN_RECORD')
    validate_checkpoint(f,w,k,args.model,args.precision,revision,ih);done+=1
 if done==n:print('E4_CELL_ALREADY_COMPLETE',done,'/',n);return
 if args.check_only:print('E4_PREFLIGHT_PASS',len(ws),'windows; checkpoint subset',n,'existing',done);return
 idle()
 import torch,transformers,bitsandbytes
 from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig
 assert torch.cuda.is_available(),'CUDA_UNAVAILABLE'
 assert torch.__version__=='2.10.0+cu128' and transformers.__version__=='5.22.2' and bitsandbytes.__version__=='0.50.2','MODEL_STACK_DRIFT'
 tok=AutoTokenizer.from_pretrained(args.model,revision=revision,use_fast=True,trust_remote_code=False)
 random.seed(cfg['seed']);torch.manual_seed(cfg['seed']);torch.cuda.manual_seed_all(cfg['seed'])
 load=dict(revision=revision,trust_remote_code=False,device_map={'':0},dtype=torch.bfloat16,attn_implementation='sdpa',low_cpu_mem_usage=True)
 if args.precision=='fp4':load['quantization_config']=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='fp4',bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_use_double_quant=False)
 model=AutoModelForCausalLM.from_pretrained(args.model,**load).eval()
 assert not any(p.device.type=='cpu' for p in model.parameters()),'CPU_OFFLOAD'
 if args.precision=='fp4':
  assert any('Linear4bit' in type(m).__name__ for m in model.modules()),'FP4_LAYERS_MISSING'
  qcfg=getattr(model.config,'quantization_config',None)
  qtype=(qcfg.get('bnb_4bit_quant_type') if isinstance(qcfg,dict) else getattr(qcfg,'bnb_4bit_quant_type',None))
  assert qtype=='fp4','FP4_CONFIG_MISMATCH'
  actual=[getattr(getattr(m,'weight',None),'quant_state',None) for m in model.modules() if 'Linear4bit' in type(m).__name__]
  assert actual and all(q is not None and getattr(q,'quant_type',None)=='fp4' for q in actual),'FP4_ACTUAL_QUANT_STATE_MISMATCH'
 env={'torch':torch.__version__,'transformers':transformers.__version__,'bitsandbytes':bitsandbytes.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'revision':revision}
 ef=base/'environment.json'
 if ef.exists() and read(ef)!=env:raise RuntimeError('ENVIRONMENT_DRIFT')
 if not meta.exists():write(meta,identity)
 if not ef.exists():write(ef,env)
 try:
  for w in subset:
   for k in range(8):
    f=base/f'example_{k}'/(w['window_id']+'.json')
    if f.exists():continue
    text=prompt(w,k)
    enc=chat_input_ids(tok.apply_chat_template(model_messages(args.model,text),tokenize=True,add_generation_prompt=True,return_tensors='pt'))
    if enc.shape[1]>8192:raise RuntimeError('INPUT_TOO_LONG')
    lim=getattr(model.config,'max_position_embeddings',None)
    if isinstance(lim,int) and enc.shape[1]+96>lim:raise RuntimeError('CONTEXT_TOO_LONG')
    enc=enc.to('cuda:0');torch.cuda.synchronize();t0=time.perf_counter()
    with torch.inference_mode(): seq=model.generate(input_ids=enc,do_sample=False,num_beams=1,max_new_tokens=96,pad_token_id=tok.eos_token_id,use_cache=True)
    torch.cuda.synchronize();dt=time.perf_counter()-t0
    output=seq[0,enc.shape[1]:];raw=tok.decode(output,skip_special_tokens=True);p=parse(raw)
    r={**checkpoint_expected(w,k,args.model,args.precision,revision,ih),'raw':raw,'raw_sha256':digest(raw),'valid':p['valid'],'indices':p['indices'],'error':p['error'],'input_tokens':int(enc.shape[1]),'generated_tokens':int(len(output)),'generation_cap_reached':len(output)>=96,'latency_seconds':round(dt,5)}
    r['record_sha256']=digest(r);write(f,r);done+=1
    print('E4_PROGRESS',args.model,args.precision,done,'/',n,'valid',p['valid'],flush=True)
 finally:
  del model,tok;gc.collect();torch.cuda.empty_cache()
 print('E4_CELL_PASS',args.model,args.precision,done,'/',n)

def main():
 p=argparse.ArgumentParser();p.add_argument('--inputs',required=True);p.add_argument('--gate',required=True);p.add_argument('--config',required=True);p.add_argument('--model',required=True);p.add_argument('--precision',choices=['fp4'],required=True);p.add_argument('--out',required=True);p.add_argument('--limit',type=int,default=0);p.add_argument('--check-only',action='store_true');a=p.parse_args();run(a)
if __name__=='__main__':main()
