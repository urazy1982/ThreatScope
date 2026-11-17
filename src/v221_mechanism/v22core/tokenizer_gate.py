"""Real local CPU tokenizer gate for v2.2 Arms B and C.

Requires transformers/model tokenizers in Ubuntu-Qua; no pretrained weights or CUDA.
Fails closed for tokenizer boundary mismatches, unexpected EOS markers or > context.
"""
from __future__ import annotations
import json,zipfile,hashlib
from pathlib import Path
from .core import SYS,SYS_SINGLE,prompt
from .constraints import TokenTrie
from .scoring import encode_continuations,END_MARKER


def model_messages(model,text,sys):
    if model.startswith('mistralai/'):
        return [{'role':'user','content':'TASK RULES:\n'+sys+'\n\nUNTRUSTED TARGET INPUT:\n'+text}]
    return [{'role':'system','content':sys},{'role':'user','content':text}]

def extract_ids(enc):
    if hasattr(enc,'get') and enc.get('input_ids') is not None:enc=enc['input_ids']
    if hasattr(enc,'shape'):
        if len(enc.shape)!=2 or enc.shape[0]!=1:raise RuntimeError('CHAT_ENCODE_SHAPE')
        return [int(i) for i in enc[0].tolist()]
    if isinstance(enc,list):
        if len(enc)==1 and isinstance(enc[0],list):return list(map(int,enc[0]))
        if enc and all(isinstance(x,int) for x in enc):return enc
    raise RuntimeError('CHAT_ENCODE_UNKNOWN_TYPE '+repr(type(enc)))

def apply_chat(tok,messages,add_generation_prompt):
    return extract_ids(tok.apply_chat_template(messages,tokenize=True,
                 add_generation_prompt=add_generation_prompt,return_tensors='pt'))

def continuation_matches_full(prefix,candidate,full,newline_ids):
    """Accept exact assistant turn or that turn plus precisely one newline.

    The newline is not part of the scored candidate, and no other suffix,
    altered candidate token, or template mismatch is accepted.
    """
    expected=list(prefix)+list(candidate)
    return list(full)==expected or (bool(newline_ids) and
                   list(full)==expected+list(newline_ids))

def preflight(archive,max_context=8192):
    from transformers import AutoTokenizer
    with zipfile.ZipFile(archive) as z:
        cfg=json.loads(z.read('config/study.json'))
        manifest=json.loads(z.read('outputs/prepared/manifest.json'))
        raw=z.read('outputs/prepared/inputs.jsonl')
    if hashlib.sha256(raw).hexdigest()!=manifest['input_sha256']:raise RuntimeError('DATASET_INPUT_DRIFT')
    windows=[json.loads(x) for x in raw.decode().splitlines() if x.strip()]
    if len(windows)!=144:raise RuntimeError('WINDOWS_MISSING')
    results=[]
    for model,revision in cfg['models'].items():
        tok=AutoTokenizer.from_pretrained(model,revision=revision,use_fast=True,trust_remote_code=False)
        eid=tok.convert_tokens_to_ids(END_MARKER[model])
        trie=TokenTrie(lambda s:tok.encode(s,add_special_tokens=False),
            lambda ids:tok.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False),eid)
        cands=encode_continuations(tok,model)
        unequal_B=unequal_C=bad_alignment=0;maximum_B=maximum_C=0
        for w in windows:
            lengths_B=[];lengths_C=[]
            for e in range(8):
                content=prompt(w,e)
                B=model_messages(model,content,SYS)
                C=model_messages(model,content,SYS_SINGLE)
                Bids=apply_chat(tok,B,True)
                Cids=apply_chat(tok,C,True)
                lengths_B.append(len(Bids));lengths_C.append(len(Cids))
                maximum_B=max(maximum_B,len(Bids));maximum_C=max(maximum_C,len(Cids))
                # The candidate scoring continuation MUST be exactly what the
                # tokenizer's full assistant turn would serialize after the prefix.
                for ci,candidate in enumerate(cands):
                    # independent of anchor e except the prompt tokens
                    full=apply_chat(tok,C+[{'role':'assistant','content':'{"relevant":['+str(ci)+']}'}],False)
                    # A few chat templates (notably Qwen) serialize one final
                    # newline *after* the assistant end-of-turn marker. This
                    # newline is outside the scored candidate and must never
                    # be included in the likelihood sum.
                    if not continuation_matches_full(Cids,candidate,full,
                            tok.encode(chr(10),add_special_tokens=False)):
                        bad_alignment+=1
            if len(set(lengths_B))!=1:unequal_B+=1
            if len(set(lengths_C))!=1:unequal_C+=1
        if maximum_B+cfg['max_new_tokens']>max_context or maximum_C+max(len(x) for x in cands)>max_context:
            raise RuntimeError('CONTEXT_TOO_LONG '+model)
        if unequal_B or unequal_C or bad_alignment:raise RuntimeError('PROMPT_TOKEN_GATE_FAIL '+model+' '+str((unequal_B,unequal_C,bad_alignment)))
        results.append({'model':model,'revision':revision,'max_tokens_B':maximum_B,'max_tokens_C':maximum_C,
          'unequal_B':unequal_B,'unequal_C':unequal_C,'candidate_token_lengths':[len(x) for x in cands],
          'full_template_alignment_errors':bad_alignment,'B_canonical_token_trie':trie.summary(),
          'status':'PASS'})
    return {'status':'V22_REAL_CPU_TOKENIZER_PREFLIGHT_PASS','dataset_sha256':manifest['dataset_sha256'],
        'input_sha256':manifest['input_sha256'],'models':results,
        'note':'This checks tokenizer compatibility only; GPU inference requires a separately approved frozen release.'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();r=preflight(a.archive)
    Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
