#!/usr/bin/env python3
"""E2: constrained GREEDY among the exact eight historical Arm C singleton suffixes.

E2 does not modify Arm C. Same historical SYS_SINGLE, prompt, chat template and
8 canonical continuations with model-specific end-of-turn; only search differs.
No GPU operations during --preflight-only. Designed for the existing 5090 stack.
"""
import argparse
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path
from importlib import metadata

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vendor.e1_neutral_gpu import verify_frozen_inputs, sha, canonical, atomic
from vendor.v22core.core import SYS_SINGLE, prompt, parse, original_effect
from vendor.v22core.tokenizer_gate import model_messages, extract_ids, continuation_matches_full
from vendor.v22core.scoring import END_MARKER, encode_continuations

PROTOCOL_ID='ThreatScope-E2-v0.1.2-matched-singleton-greedy-vs-archived-scoring'
STACK={'torch':'2.10.0+cu128','transformers':'5.22.2','bitsandbytes':'0.50.2'}

class SingletonTrie:
    """Allowed tokens are precisely the eight frozen JSON strings + EOT."""
    def __init__(self,continuations):
        if len(continuations)!=8 or len({tuple(c) for c in continuations})!=8:
            raise ValueError('EIGHT_DISTINCT_SUFFIXES_REQUIRED')
        self.candidates={tuple(map(int,c)) for c in continuations}
        self.root={}
        for c in self.candidates:
            if not c or any(type(t)!=int or t<0 for t in c):raise ValueError('BAD_SUFFIX')
            node=self.root
            for token in c:node=node.setdefault(token,{})
        if any(a != b and a == b[:len(a)] for a in self.candidates for b in self.candidates):
            raise RuntimeError('AMBIGUOUS_CANDIDATE_PREFIX')
    def allowed(self,prefix):
        node=self.root
        for t in prefix:
            if t not in node:return ()
            node=node[t]
        return tuple(sorted(node))
    def accepts(self,tokens):
        return tuple(tokens) in self.candidates



def normalize_chat_input(enc, torch_module, expected_ids=None):
    """Normalize tokenizer chat-template outputs to a single torch LongTensor.

    transformers versions may return a flat list, a BatchEncoding/dict, or an
    already batched Tensor even when return_tensors='pt' is requested. We
    deliberately reuse the historical strict token-ID extractor, preserving
    every token; no padding, truncation or extra special tokens are introduced.
    """
    ids=extract_ids(enc)
    if not ids or any(type(x)!=int or x<0 for x in ids):
        raise RuntimeError('BAD_CHAT_TOKEN_IDS')
    if expected_ids is not None and ids!=list(expected_ids):
        raise RuntimeError('CHAT_INPUT_TOKEN_DRIFT')
    tensor=torch_module.tensor([ids],dtype=torch_module.long)
    if tensor.ndim!=2 or tensor.shape[0]!=1 or tensor.shape[1]!=len(ids):
        raise RuntimeError('BAD_CHAT_INPUT_TENSOR')
    return tensor

def validate_protocol(inputs,manifest,model,precision):
    m,windows,cfg=verify_frozen_inputs(inputs,manifest,model)
    if precision not in ('bf16','nf4') or precision not in cfg['precisions']:
        raise RuntimeError('PRECISION_NOT_FROZEN')
    if len(windows)!=144 or sum(len(x['sentences']) for x in windows)!=1152:
        raise RuntimeError('FROZEN_FRAME_MISMATCH')
    # Historical Arm C source code, imported unchanged from v2.2.1.
    for w in windows:
        for k in range(8):
            p=prompt(w,k)
            if '"relevant":['+str(k)+']' not in p:
                raise RuntimeError('HISTORICAL_PROMPT_INDEX_MISSING')
    return m,windows,cfg


def identity_for(manifest,config,model,precision,script):
    rev=config['models'][model]
    return {'protocol':PROTOCOL_ID,'model':model,'revision':rev,
            'precision':precision,'input_sha256':manifest['input_sha256'],
            'manifest_sha256':hashlib.sha256(Path(script[0]).read_bytes()).hexdigest(),
            'historical_sys_single_sha256':sha(SYS_SINGLE),
            'original_prompt_source_sha256':hashlib.sha256((ROOT/'vendor/v22core/core.py').read_bytes()).hexdigest(),
            'original_tokenizer_gate_source_sha256':hashlib.sha256((ROOT/'vendor/v22core/tokenizer_gate.py').read_bytes()).hexdigest(),
            'original_scoring_source_sha256':hashlib.sha256((ROOT/'vendor/v22core/scoring.py').read_bytes()).hexdigest(),
            'runner_source_sha256':hashlib.sha256(Path(script[1]).read_bytes()).hexdigest(),
            'search':'token-trie-constrained-left-to-right-greedy',
            'candidate_space':'eight canonical singleton JSON strings + exact EOT',
            'seed':20261113,'do_sample':False,'num_beams':1,
            'max_new_tokens':'exact frozen maximum candidate suffix length',
            'stack':STACK}


def check_record(r,ident,w,anchor,expected_prompt_hash,candidates):
    expect={'protocol':PROTOCOL_ID,'model':ident['model'],'precision':ident['precision'],
            'window_id':w['window_id'],'anchor':anchor,'revision':ident['revision'],
            'input_sha256':w['input_sha256'],'identity_sha256':sha(canonical(ident)),
            'prompt_sha256':expected_prompt_hash}
    for k,v in expect.items():
        if r.get(k)!=v:raise RuntimeError('CHECKPOINT_FIELD_DRIFT '+k)
    raw=r.get('raw');tokens=r.get('generated_ids');idx=r.get('selected_index')
    if not isinstance(raw,str) or not isinstance(tokens,list) or not all(type(x)==int for x in tokens):
        raise RuntimeError('CHECKPOINT_MALFORMED')
    if tuple(tokens) not in {tuple(c) for c in candidates}:
        raise RuntimeError('CHECKPOINT_NONCANONICAL_SUFFIX')
    if r.get('raw_sha256')!=sha(raw):raise RuntimeError('CHECKPOINT_RAW_DRIFT')
    if type(idx)!=int or idx not in range(8) or r.get('valid') is not True or raw!='{"relevant":['+str(idx)+']}' or tokens!=list(candidates[idx]):
        raise RuntimeError('CHECKPOINT_DECISION_DRIFT')
    if r.get('record_sha256')!=sha(canonical({k:v for k,v in r.items() if k!='record_sha256'})):
        raise RuntimeError('CHECKPOINT_SHA256_DRIFT')
    return True


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--inputs',type=Path,required=True)
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--model',required=True)
    ap.add_argument('--precision',choices=['bf16','nf4'],required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--limit',type=int,default=0,help='0=all 144 windows; 2=smoke')
    ap.add_argument('--preflight-only',action='store_true')
    a=ap.parse_args()
    if a.limit<0 or a.limit>144:raise RuntimeError('BAD_LIMIT')
    manifest,windows,cfg=validate_protocol(a.inputs,a.manifest,a.model,a.precision)
    ident=identity_for(manifest,cfg,a.model,a.precision,(a.manifest,__file__))
    selected=windows[:a.limit] if a.limit else windows
    if a.preflight_only:
        print('E2_FROZEN_CPU_PREFLIGHT_PASS',json.dumps({'model':a.model,'precision':a.precision,
              'windows':len(windows),'selected':len(selected),'anchors':8,
              'input_sha256':manifest['input_sha256'],'protocol':PROTOCOL_ID}))
        return
    import torch, transformers, bitsandbytes
    from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig
    if not torch.cuda.is_available():raise RuntimeError('CUDA_REQUIRED')
    installed={'torch':torch.__version__,'transformers':transformers.__version__,'bitsandbytes':bitsandbytes.__version__}
    if installed!=STACK:raise RuntimeError('GPU_STACK_DRIFT '+str(installed))
    if torch.cuda.get_device_properties(0).total_memory < 20_000_000_000:raise RuntimeError('INSUFFICIENT_VRAM')
    out=a.out
    if out.exists() and (out/'identity.json').exists() and json.loads((out/'identity.json').read_text())!=ident:
        raise RuntimeError('RESUME_IDENTITY_DRIFT')
    if out.exists() and not (out/'identity.json').exists() and list(out.glob('windows/**/*.json')):
        raise RuntimeError('ORPHAN_CHECKPOINTS')
    out.mkdir(parents=True,exist_ok=True)
    atomic(out/'identity.json',ident)
    rev=cfg['models'][a.model]
    tok=AutoTokenizer.from_pretrained(a.model,revision=rev,use_fast=True,trust_remote_code=False)
    continuations=encode_continuations(tok,a.model)
    trie=SingletonTrie(continuations)
    eot=tok.convert_tokens_to_ids(END_MARKER[a.model]);assert all(c[-1]==eot for c in continuations)
    lengths=[len(c) for c in continuations]
    if len(set(lengths))!=1 or max(lengths)>96:
        raise RuntimeError('HISTORICAL_SINGLETON_CANDIDATE_LENGTH_GATE')
    # Validate chat-turn serialization with one prompt and every exact candidate.
    sample_messages=model_messages(a.model,prompt(windows[0],0),SYS_SINGLE)
    # Use the frozen historical tokenizer gate's canonical ID extraction and
    # exact continuation alignment. The full chat template may append a single
    # newline AFTER the EOT; this newline is NOT part of any scored candidate.
    gen_prefix=extract_ids(tok.apply_chat_template(sample_messages,tokenize=True,add_generation_prompt=True))
    newline=tok.encode('\n',add_special_tokens=False)
    for j,c in enumerate(continuations):
        full=extract_ids(tok.apply_chat_template(sample_messages+[{'role':'assistant','content':'{"relevant":['+str(j)+']}'}],tokenize=True,add_generation_prompt=False))
        if not continuation_matches_full(gen_prefix,c,full,newline):
            raise RuntimeError('HISTORICAL_ARM_C_SUFFIX_ALIGNMENT_FAIL '+str(j))
    kw={'revision':rev,'trust_remote_code':False,'device_map':{'':0},'dtype':torch.bfloat16,
        'attn_implementation':'sdpa','low_cpu_mem_usage':True}
    if a.precision=='nf4':
        kw['quantization_config']=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_use_double_quant=False)
    model=AutoModelForCausalLM.from_pretrained(a.model,**kw).eval()
    if any(p.device.type!='cuda' for p in model.parameters()):raise RuntimeError('CPU_OFFLOAD')
    from bitsandbytes.nn import Linear4bit
    linear4=[m for m in model.modules() if isinstance(m,Linear4bit)]
    if a.precision=='nf4' and (not linear4 or any(getattr(m.weight,'quant_type',None)!='nf4' for m in linear4)):
        raise RuntimeError('NF4_NOT_ACTUALLY_LOADED')
    if a.precision=='bf16' and linear4:raise RuntimeError('BF16_CONTAINS_4BIT_MODULES')
    mc=getattr(model.config,'_commit_hash',None);tc=tok.init_kwargs.get('_commit_hash')
    if mc is not None and mc!=rev or tc is not None and tc!=rev:
        raise RuntimeError('MODEL_OR_TOKENIZER_REVISION_DRIFT')
    provenance={'model':a.model,'revision':rev,'precision':a.precision,
       'model_commit':mc,'tokenizer_commit':tc,'tokenizer_chat_template_sha256':sha(str(tok.chat_template)),
       'gpu':torch.cuda.get_device_name(0),'cuda':torch.version.cuda,
       'verified_linear4bit_modules':len(linear4),'candidate_token_lengths':lengths,
       'stack':installed,'extra_dependencies':{name:metadata.version(name) for name in ('huggingface-hub','tokenizers','accelerate','safetensors','numpy')}}
    pp=out/'load_provenance.json'
    if pp.exists() and json.loads(pp.read_text())!=provenance:raise RuntimeError('LOAD_PROVENANCE_DRIFT')
    atomic(pp,provenance)
    random.seed(20261113);torch.manual_seed(20261113);torch.cuda.manual_seed_all(20261113)
    done=0
    for i,w in enumerate(selected):
        for anchor in range(8):
            msgs=model_messages(a.model,prompt(w,anchor),SYS_SINGLE)
            ph=sha(canonical(msgs))
            dest=out/'windows'/w['window_id']/f'anchor_{anchor}.json'
            encoded=tok.apply_chat_template(msgs,tokenize=True,add_generation_prompt=True,return_tensors='pt')
            # Exact historical token stream, normalized to [batch=1, tokens].
            # Never call the tokenizer again with a different chat template.
            ids=normalize_chat_input(encoded,torch)
            limit=getattr(model.config,'max_position_embeddings',None)
            if ids.shape[1]>cfg.get('max_input_tokens',8192) or not isinstance(limit,int) or ids.shape[1]+max(lengths)>limit:
                raise RuntimeError('CONTEXT_LIMIT')
            if dest.exists():
                check_record(json.loads(dest.read_text()),ident,w,anchor,ph,continuations)
                done+=1;continue
            prefix_len=ids.shape[1]
            def allowed(batch_id,input_ids):
                if batch_id!=0:raise RuntimeError('UNEXPECTED_BATCH')
                suffix=input_ids[prefix_len:].tolist()
                seq=trie.allowed(suffix)
                if not seq:raise RuntimeError('TRIE_NO_CONTINUATION '+str(suffix))
                return list(seq)
            t0=time.monotonic()
            with torch.inference_mode():
                output=model.generate(ids.to('cuda:0'),do_sample=False,num_beams=1,
                    max_new_tokens=max(lengths),eos_token_id=eot,pad_token_id=tok.eos_token_id,
                    prefix_allowed_tokens_fn=allowed,use_cache=True)
            generated=output[0,prefix_len:].tolist()
            if not trie.accepts(generated):raise RuntimeError('OUTPUT_OUTSIDE_MATCHED_SINGLETON_SPACE')
            raw=tok.decode(generated,skip_special_tokens=True,clean_up_tokenization_spaces=False)
            parsed=parse(raw)
            if not parsed['valid'] or len(parsed['indices'])!=1:
                raise RuntimeError('OUTPUT_PARSE_FAILED')
            rec={'protocol':PROTOCOL_ID,'model':a.model,'precision':a.precision,'revision':rev,
                 'window_id':w['window_id'],'source':w['source'],'report_id':w['report_id'],
                 'anchor':anchor,'input_sha256':w['input_sha256'],'identity_sha256':sha(canonical(ident)),
                 'prompt_sha256':ph,'generated_ids':generated,'raw':raw,'raw_sha256':sha(raw),
                 'selected_index':parsed['indices'][0],'valid':True,
                 'prompt_tokens':prefix_len,'generated_tokens':len(generated),
                 'elapsed_seconds':round(time.monotonic()-t0,4)}
            rec['record_sha256']=sha(canonical(rec))
            check_record(rec,ident,w,anchor,ph,continuations)
            atomic(dest,rec)
            done+=1
            print('E2_GREEDY',a.model,a.precision,done,'/',len(selected)*8,'anchor',anchor,flush=True)
    atomic(out/'cell_status.json',{'protocol':PROTOCOL_ID,'model':a.model,'precision':a.precision,
        'window_count':len(selected),'completed':done,'full_cell':len(selected)==144,
        'expected':len(selected)*8,'identity_sha256':sha(canonical(ident))})
    print('E2_CELL_PASS',a.model,a.precision,'records',done)

if __name__=='__main__':main()
