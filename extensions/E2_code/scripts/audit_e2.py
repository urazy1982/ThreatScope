#!/usr/bin/env python3
"""CPU-only independent checkpoint and actual-tokenizer audit for E2; no model weights."""
import argparse,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vendor.e1_neutral_gpu import verify_frozen_inputs,sha,canonical,atomic
from vendor.v22core.core import SYS_SINGLE,prompt
from vendor.v22core.tokenizer_gate import model_messages
from vendor.v22core.scoring import encode_continuations
from scripts.e2_singleton_gpu import check_record, identity_for

def audit(inputs,manifest,model,precision,out,limit=0):
    m,windows,cfg=verify_frozen_inputs(inputs,manifest,model)
    selected=windows[:limit] if limit else windows
    ident=identity_for(m,cfg,model,precision,(manifest,ROOT/'scripts/e2_singleton_gpu.py'))
    if json.loads((out/'identity.json').read_text(encoding='utf-8'))!=ident:
        raise RuntimeError('IDENTITY_DRIFT')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(model,revision=cfg['models'][model],local_files_only=True,use_fast=True,trust_remote_code=False)
    cands=encode_continuations(tok,model)
    count=0
    for w in selected:
        for anchor in range(8):
            path=out/'windows'/w['window_id']/f'anchor_{anchor}.json'
            if not path.is_file():raise RuntimeError('MISSING_CHECKPOINT '+str(path))
            r=json.loads(path.read_text(encoding='utf-8'))
            ph=sha(canonical(model_messages(model,prompt(w,anchor),SYS_SINGLE)))
            check_record(r,ident,w,anchor,ph,cands);count+=1
    expected=len(selected)*8
    if count!=expected:raise RuntimeError('COUNT_MISMATCH')
    return {'status':'E2_CHECKPOINT_TOKENIZER_AUDIT_PASS','model':model,'precision':precision,
            'windows':len(selected),'records':count,'full_cell':len(selected)==144,
            'input_sha256':m['input_sha256'],'candidate_lengths':[len(c) for c in cands]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--model',required=True);ap.add_argument('--precision',choices=['bf16','nf4'],required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--limit',type=int,default=0)
    a=ap.parse_args()
    if a.limit<0 or a.limit>144:raise RuntimeError('INVALID_LIMIT')
    r=audit(a.inputs,a.manifest,a.model,a.precision,a.out,a.limit)
    atomic(a.out/'audit_status.json',r)
    print(json.dumps(r,indent=2))

if __name__=='__main__':main()
