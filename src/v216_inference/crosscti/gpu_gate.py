"""Dataset-bound final CPU authorization for the frozen 9-publisher study."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from .core import read,write,digest
from .analyze import verify_prepared

EXPECTED_DATASET='461682f329a5cca95715d6d7a12356dddb3f38f3adf0e221a2443bdecfdd354e'
EXPECTED_SOURCE_REV='c06c0183be808d2e7b2bcbdb351426b75c8cde0f'
EXPECTED_INDEX='3275d2c19071d800bf3e0147105e66114b2aa94025576cd43e187edcff78ce12'
EXPECTED_ARCHIVE='c8b1cd2a66aadb6943b67cb79fd24ff29bd5a3389f33fa050222b08da35c637c'
EXPECTED_SMAH='00e606241dfdb3f57d5a2e25c9b696a4c3d5090d376f47047cce3fa53b503d97'
CRITICAL=('crosscti/core.py','crosscti/prepare.py','crosscti/analyze.py','crosscti/runner.py','crosscti/token_encoding.py','crosscti/preflight.py','crosscti/final_cpu_gate.py','crosscti/gpu_gate.py','corpusapt/acquire.py')

def hfile(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()

def identity(root):
    root=Path(root)
    cfg,m,windows=verify_prepared(root)
    prov=read(root/'dataset/corpus_provenance.json')
    if m['dataset_sha256']!=EXPECTED_DATASET:raise RuntimeError('FROZEN_DATASET_MISMATCH')
    if len(windows)!=144 or m['total_calls']!=6912 or len(cfg['source_names'])!=9:raise RuntimeError('DESIGN_DRIFT')
    if cfg.get('anchor_indices')!=list(range(8)) or cfg.get('precisions')!=['bf16','nf4'] or cfg.get('max_new_tokens')!=96:raise RuntimeError('EXECUTION_DESIGN_DRIFT')
    if set(cfg['models'])!={'Qwen/Qwen2.5-3B-Instruct','mistralai/Mistral-7B-Instruct-v0.3','meta-llama/Llama-3.2-3B-Instruct'}:raise RuntimeError('MODEL_SET_DRIFT')
    if cfg.get('source_provenance_status')!='COLLECTOR_INDEX_ARCHIVE_MATCHED_CPU_ONLY':raise RuntimeError('SOURCE_STATUS_DRIFT')
    if prov.get('revision')!=EXPECTED_SOURCE_REV or prov.get('index_sha256')!=EXPECTED_INDEX or prov.get('archive_sha256')!=EXPECTED_ARCHIVE or prov.get('smah_inputs_sha256')!=EXPECTED_SMAH:raise RuntimeError('SOURCE_PROVENANCE_DRIFT')
    if prov.get('overlap_repair_status')!='FULL_REPORT_SENTENCE_EXCLUSION_PASS':raise RuntimeError('REPAIR_STATUS_DRIFT')
    code_hashes={n:hfile(root/n) for n in CRITICAL}
    return {'protocol':cfg['protocol'],'dataset_sha256':m['dataset_sha256'],'input_sha256':m['input_sha256'],'config_sha256':m['config_sha256'],'smah_sha256':EXPECTED_SMAH,'source_revision':EXPECTED_SOURCE_REV,'source_index_sha256':EXPECTED_INDEX,'archive_sha256':EXPECTED_ARCHIVE,'source_names':list(cfg['source_names']),'models':dict(cfg['models']),'precisions':cfg['precisions'],'anchors':cfg['anchor_indices'],'max_new_tokens':cfg['max_new_tokens'],'code_sha256':code_hashes,'window_count':len(windows),'calls':m['total_calls']}

def verify_authorization(root):
    root=Path(root);path=root/'outputs/authorization/gpu_authorization.json'
    if not path.is_file():raise RuntimeError('GPU_AUTHORIZATION_MISSING')
    doc=read(path)
    sig=doc.get('authorization_sha256')
    if not isinstance(sig,str) or sig!=digest({k:v for k,v in doc.items() if k!='authorization_sha256'}):raise RuntimeError('AUTHORIZATION_TAMPERED')
    if doc.get('status')!='GPU_AUTHORIZED_DATASET_BOUND':raise RuntimeError('GPU_NOT_AUTHORIZED')
    if doc.get('identity')!=identity(root):raise RuntimeError('GPU_AUTHORIZATION_INPUT_DRIFT')
    p=doc.get('preflight')
    if not isinstance(p,list) or len(p)!=3 or {v.get('model') for v in p}!=set(doc['identity']['models']):raise RuntimeError('PREFLIGHT_AUTHORIZATION_INVALID')
    if any(v.get('ok') is not True or v.get('unequal_windows')!=0 or not 64<=v.get('max_input_tokens',0)<=8192 for v in p):raise RuntimeError('PREFLIGHT_INVALID')
    return doc

def authorize(root,smah):
    from .final_cpu_gate import validate
    from .preflight import run
    root=Path(root)
    baseline=Path(smah)
    if hfile(baseline)!=EXPECTED_SMAH:raise RuntimeError('SMAH_INPUT_HASH_CHANGED')
    report=validate(root,baseline)
    if report['status']!='CPU_AUDIT_PASS_NEAR_DUP_SCREEN_ONLY' or report['near_duplicate_flag_count'] or report['exact_overlap_full_apt_vs_smah_windows'] or report['reports']!=72 or report['windows']!=144:raise RuntimeError('FINAL_CPU_AUDIT_NOT_PASS')
    preflight=run(root)
    rec={'status':'GPU_AUTHORIZED_DATASET_BOUND','identity':identity(root),'preflight':preflight,'cpu_audit_status':report['status'],'near_duplicate_flags':report['near_duplicate_flag_count'],'limitations':['SMAH comparison is limited to archived selected windows, not full historical reports','Shingle screen does not prove semantic independence','No inference claims prior to actual GPU checkpoints']}
    rec['authorization_sha256']=digest(rec)
    write(root/'outputs/authorization/gpu_authorization.json',rec)
    verify_authorization(root)
    return rec

def main():
    a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--smah-inputs');a.add_argument('--verify-only',action='store_true');args=a.parse_args()
    if args.verify_only:doc=verify_authorization(args.root)
    else:
        if not args.smah_inputs:raise ValueError('SMAH_INPUTS_REQUIRED')
        doc=authorize(args.root,args.smah_inputs)
    print(json.dumps({'status':doc['status'],'calls':doc['identity']['calls'],'dataset_sha256':doc['identity']['dataset_sha256'],'preflight':doc['preflight'],'authorization_sha256':doc['authorization_sha256']},indent=2))
if __name__=='__main__':main()
