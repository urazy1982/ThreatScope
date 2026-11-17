#!/usr/bin/env python3
"""CPU-only fail-closed E1 launch authorization; no model inference or GPU load."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from e1_neutral_gpu import verify_frozen_inputs, PROTOCOL_ID
from orchestrate_e1 import MODELS
from audit_e1 import verify_cell


def check_c8_hamming_aggregate(model_summary):
    """Reject internally contradictory per-regime and overall C8 pair statistics."""
    by_instruction=model_summary.get('by_instruction',{})
    if set(by_instruction)!={'B','C'}:
        raise RuntimeError('INCOMPLETE_C8_INSTRUCTION_REGIMES')
    for regime in ('B','C'):
        cell=by_instruction[regime]
        pairs=cell.get('pairs',-1)
        if pairs!=4032 or sum(cell.get(k,0) for k in ('unequal','one','multi','zero'))!=pairs:
            raise RuntimeError('C8_PAIRWISE_COUNT_INCONSISTENT '+regime)
        maximum=cell.get('max_hamming',-1)
        if maximum<0 or (cell.get('multi',0)==0 and maximum>1) or (cell.get('one',0)==pairs and maximum!=1):
            raise RuntimeError('C8_MAX_HAMMING_INCONSISTENT '+regime)
    for overall, per_regime in (('one_token_hamming_pairs','one'),
                               ('more_than_one_token_changed_pairs','multi'),
                               ('unequal_length_pairs','unequal')):
        if model_summary.get(overall)!=sum(by_instruction[r].get(per_regime,0) for r in ('B','C')):
            raise RuntimeError('C8_AGGREGATE_COUNT_MISMATCH '+overall)
    if model_summary.get('max_hamming_distance')!=max(by_instruction[r]['max_hamming'] for r in ('B','C')):
        raise RuntimeError('C8_AGGREGATE_MAXIMUM_MISMATCH')
    return True


def verify(inputs,manifest,results,root,mode):
    m,windows,cfg=verify_frozen_inputs(inputs,manifest)
    gate=results/'preflight/C8_actual_tokenizer_ids.json'
    if not gate.is_file():raise RuntimeError('C8_TOKENIZER_ID_CHECK_REQUIRED')
    r=json.loads(gate.read_text(encoding='utf-8'))
    codehash=hashlib.sha256((root/'scripts/c8_prompt_gate.py').read_bytes()).hexdigest()
    actual_config=hashlib.sha256((manifest.parent.parent.parent/'config/study.json').read_bytes()).hexdigest()
    if (r.get('status')!='TOKENIZER_ID_MEASURED_AND_RECORDED' or
        r.get('tokenizer_id_status')!='PASS_OBSERVED_TOKENIZER_COMPARISON' or
        r.get('input_sha256')!=m['input_sha256'] or
        r.get('config_sha256')!=m['config_sha256'] or
        r.get('tokenizer_gate_script_sha256')!=codehash or
        actual_config!=m['config_sha256']):
        raise RuntimeError('STALE_OR_WRONG_C8_TOKENIZER_CERTIFICATION')
    by_model={x['model']:x for x in r.get('models',[])}
    if len(by_model)!=3 or set(by_model)!=set(MODELS):
        raise RuntimeError('WRONG_TOKENIZER_MODEL_FAMILIES')
    for model,rev in cfg['models'].items():
        x=by_model.get(model,{})
        if x.get('revision')!=rev or x.get('total_prompt_comparisons')!=8064 or x.get('unequal_length_pairs')!=0:
            raise RuntimeError('C8_TOKENIZER_COVERAGE_OR_REVISION_DRIFT '+model)
        if x.get('observed_tokenizer_commit') not in (rev,None):
            raise RuntimeError('ACTUAL_TOKENIZER_REVISION_MISMATCH '+model)
        if set(x.get('by_instruction',{}))!={'B','C'} or any(x['by_instruction'][regime].get('pairs')!=4032 for regime in ('B','C')):
            raise RuntimeError('INCOMPLETE_PAIRWISE_TOKENIZER_GATE '+model)
        check_c8_hamming_aggregate(x)
    if mode=='full':
        model='Qwen/Qwen2.5-3B-Instruct'
        d=results/'E1'/MODELS[model]/'bf16'/'N0'
        smoke=verify_cell(d,model,'bf16','N0',windows,m,cfg,2,
                          hashlib.sha256(manifest.read_bytes()).hexdigest(),subset_ok=True)
        if smoke['valid']!=2:raise RuntimeError('SMOKE_TWO_REAL_OUTPUTS_NOT_VALID')
    return dict(status='E1_LAUNCH_AUTHORIZATION_PASS',mode=mode,protocol=PROTOCOL_ID,
                input_sha256=m['input_sha256'],tokenizers=3,tokenizer_pairs=24192,
                smoke_verified=(mode=='full'))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--results',type=Path,required=True);p.add_argument('--mode',choices=['smoke','full'],required=True)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    print(json.dumps(verify(a.inputs,a.manifest,a.results,root,a.mode),indent=2))
