"""Resume-safe GPU evaluation, isolated from the CPU-only dataset and analysis pipeline."""
from __future__ import annotations
import argparse,gc,json,os,random,time,traceback,hashlib
from pathlib import Path
from .core import SYS,prompt,parse,read,lines,write,digest,cell_id
from .analyze import verify_prepared
from .token_encoding import chat_input_ids

def model_messages(model,text):
    if model.startswith('mistralai/'):
        return [{'role':'user','content':'TASK RULES:\n'+SYS+'\n\nUNTRUSTED TARGET INPUT:\n'+text}]
    return [{'role':'system','content':SYS},{'role':'user','content':text}]

def expected_identity(root,model,precision):
    root=Path(root);cfg,m,_=verify_prepared(root)
    return {'protocol':cfg['protocol'],'model':model,'revision':cfg['models'][model],
            'precision':precision,'prepared_input_sha256':m['input_sha256'],
            'config_sha256':m['config_sha256'],'prompt_sha256':digest(SYS),
            'decoding':{'do_sample':False,'num_beams':1,'max_new_tokens':cfg['max_new_tokens']},
            'torch_dtype':'bfloat16','attention_implementation':'sdpa',
            'python_package_lock': 'torch-transformers-bitsandbytes-versions-in-environment_metadata'}

def validate_checkpoint(path,w,k,model,precision,revision,idhash):
    r=read(path)
    expected={'window_id':w['window_id'],'input_sha256':w['input_sha256'],
              'anchor':k,'model':model,'precision':precision,'revision':revision,
              'identity_sha256':idhash,'prompt_sha256':digest([SYS,prompt(w,k),model])}
    for field,value in expected.items():
        if r.get(field)!=value:raise RuntimeError('CHECKPOINT_IDENTITY_DRIFT '+str(path)+' '+field)
    if r.get('raw_sha256')!=digest(r.get('raw','')):raise RuntimeError('RAW_TAMPER')
    if r.get('record_sha256')!=digest({a:b for a,b in r.items() if a!='record_sha256'}):
        raise RuntimeError('CHECKPOINT_TAMPER '+str(path))
    p=parse(r['raw'])
    if (r['valid'],r['indices'],r['error'])!=(p['valid'],p['indices'],p['error']):
        raise RuntimeError('PARSER_REPLAY_CHANGED '+str(path))
    return r

def run_cell(root,model,precision):
    cfg,m,windows=verify_prepared(root)
    # Authenticate the frozen corpus, model configuration, code and real CPU preflight
    # before importing CUDA libraries or creating any GPU checkpoints.
    from .gpu_gate import verify_authorization
    verify_authorization(root)
    import torch,transformers,bitsandbytes
    from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig
    if model not in cfg['models'] or precision not in cfg['precisions']:raise ValueError('INVALID_CELL')
    if not torch.cuda.is_available():raise RuntimeError('GPU_REQUIRED')
    base=Path(root)/'outputs/runs'/cell_id(model,precision)
    base.mkdir(parents=True,exist_ok=True)
    identity=expected_identity(root,model,precision)
    mp=base/'run_metadata.json';ih=digest(identity)
    if mp.exists() and read(mp)!=identity:raise RuntimeError('MODEL_METADATA_DRIFT')
    existing=0
    for w in windows:
        for k in range(8):
            f=base/f'example_{k}'/(w['window_id']+'.json')
            if f.exists():
                if not mp.exists():raise RuntimeError('ORPHAN_GPU_RECORD')
                validate_checkpoint(f,w,k,model,precision,cfg['models'][model],ih);existing+=1
    n=len(windows)*8
    if existing==n:
        print('CELL_ALREADY_COMPLETE',model,precision,n,flush=True);return
    random.seed(cfg['seed']);torch.manual_seed(cfg['seed']);torch.cuda.manual_seed_all(cfg['seed'])
    rev=cfg['models'][model];tok=AutoTokenizer.from_pretrained(model,revision=rev,use_fast=True,trust_remote_code=False)
    args=dict(revision=rev,trust_remote_code=False,device_map={'':0},dtype=torch.bfloat16,
              attn_implementation='sdpa',low_cpu_mem_usage=True)
    if precision=='nf4':
        args['quantization_config']=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',
                             bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_use_double_quant=False)
    llm=AutoModelForCausalLM.from_pretrained(model,**args).eval()
    if any(p.device.type=='cpu' for p in llm.parameters()):raise RuntimeError('CPU_OFFLOAD_DETECTED')
    if not mp.exists():write(mp,identity)
    env={'torch':torch.__version__,'transformers':transformers.__version__,'bitsandbytes':bitsandbytes.__version__,
         'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'revision':rev}
    ef=base/'environment.json'
    if ef.exists() and read(ef)!=env:raise RuntimeError('ENVIRONMENT_CHANGED')
    if not ef.exists():write(ef,env)
    done=existing
    try:
        for w in windows:
            for k in range(8):
                f=base/f'example_{k}'/(w['window_id']+'.json')
                if f.exists():continue
                text=prompt(w,k)
                enc=chat_input_ids(tok.apply_chat_template(model_messages(model,text),tokenize=True,add_generation_prompt=True,return_tensors='pt'))
                if enc.shape[1]>cfg['max_input_tokens']:raise RuntimeError('INPUT_TOO_LONG')
                limit=getattr(llm.config,'max_position_embeddings',None)
                if not isinstance(limit,int) or enc.shape[1]+cfg['max_new_tokens']>limit:raise RuntimeError('CONTEXT_LIMIT')
                enc=enc.to('cuda:0');torch.cuda.synchronize();t0=time.perf_counter()
                with torch.inference_mode():
                    seq=llm.generate(input_ids=enc,do_sample=False,num_beams=1,max_new_tokens=cfg['max_new_tokens'],
                                     pad_token_id=tok.eos_token_id,use_cache=True)
                torch.cuda.synchronize();dt=time.perf_counter()-t0
                output=seq[0,enc.shape[1]:]
                raw=tok.decode(output,skip_special_tokens=True);p=parse(raw)
                rec={'window_id':w['window_id'],'input_sha256':w['input_sha256'],'anchor':k,'model':model,
                     'precision':precision,'revision':rev,'identity_sha256':ih,
                     'prompt_sha256':digest([SYS,text,model]),'raw':raw,'raw_sha256':digest(raw),
                     'valid':p['valid'],'indices':p['indices'],'error':p['error'],
                     'input_tokens':int(enc.shape[1]),'generated_tokens':int(len(output)),
                     'generation_cap_reached':len(output)>=cfg['max_new_tokens'],
                     'latency_seconds':round(dt,5)}
                rec['record_sha256']=digest(rec);write(f,rec);done+=1
                print('COMPLETE',model,precision,f'example_{k}',f'{done}/{n}',p['valid'],flush=True)
    finally:
        del llm,tok;gc.collect();torch.cuda.empty_cache()

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--model',required=True)
    p.add_argument('--precision',choices=['bf16','nf4'],required=True);a=p.parse_args()
    run_cell(a.root,a.model,a.precision)
if __name__=='__main__':main()
