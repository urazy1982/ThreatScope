"""ThreatStudy v2.2.1 guarded real GPU handoff.

No real GPU inference is executed by importing this module. Functions not needing
transformers or model weights are intentionally CPU-only and independently tested.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,sys,time,zipfile,collections,math
from pathlib import Path
from .core import digest,parse,original_effect,exact_p,holm,SYS,SYS_SINGLE,prompt
from .replay import validate_archive
from .tokenizer_gate import model_messages,apply_chat
from .constraints import TokenTrie,canonical_language
from .scoring import END_MARKER,encode_continuations,score_candidates_serial,softmax,argmax_lowest

ARCHIVE='reference/ThreatStudy_v216_Complete_Results.zip'
EXPECTED_DATASET='461682f329a5cca95715d6d7a12356dddb3f38f3adf0e221a2443bdecfdd354e'
EXPECTED_INPUT='e22310e37efe29c2f29f8ec51b931d765a371cc9f7628b52337fa86ce338500b'
RUNS='outputs_v221'


def sha_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def release_check(root):
    root=Path(root)
    man=json.loads((root/'RELEASE_HASHES.json').read_text())['files_sha256']
    for rel,hashval in man.items():
        fp=root/rel
        if not fp.is_file() or sha_file(fp)!=hashval:
            raise RuntimeError('FROZEN_RELEASE_FILE_DRIFT '+rel)
    return man

def base(root,validate_records=True):
    root=Path(root);release_check(root)
    ap=root/ARCHIVE
    if validate_records:
        cfg,m,windows,rows,audit=validate_archive(ap)
    else:
        with zipfile.ZipFile(ap) as z:
            cfg=json.loads(z.read('config/study.json'))
            m=json.loads(z.read('outputs/prepared/manifest.json'))
            raw=z.read('outputs/prepared/inputs.jsonl')
            windows=[json.loads(s) for s in raw.decode().splitlines() if s.strip()]
        rows=None;audit=None
    if m.get('dataset_sha256')!=EXPECTED_DATASET or m.get('input_sha256')!=EXPECTED_INPUT:
        raise RuntimeError('FROZEN_DATASET_INPUT_DRIFT')
    if len(windows)!=144 or len(cfg['models'])!=3 or len(cfg['source_names'])!=9:
        raise RuntimeError('FROZEN_MATRIX_DRIFT')
    if sorted(cfg['precisions'])!=['bf16','nf4']:
        raise RuntimeError('FROZEN_PRECISION_DRIFT')
    return cfg,m,windows,rows,audit

def validate_gate(data,cfg,m):
    if data.get('status')!='V22_REAL_CPU_TOKENIZER_PREFLIGHT_PASS':
        raise RuntimeError('TOKENIZER_GATE_NOT_PASS')
    if data.get('dataset_sha256')!=EXPECTED_DATASET or data.get('input_sha256')!=EXPECTED_INPUT:
        raise RuntimeError('TOKENIZER_GATE_DATA_DRIFT')
    models=data.get('models')
    if not isinstance(models,list) or len(models)!=3 or {x.get('model') for x in models}!=set(cfg['models']):
        raise RuntimeError('TOKENIZER_MODEL_SET_DRIFT')
    for row in models:
        model=row['model']
        if row.get('status')!='PASS' or row.get('revision')!=cfg['models'][model]:
            raise RuntimeError('TOKENIZER_REVISION_DRIFT '+model)
        if any(row.get(k)!=0 for k in ('unequal_B','unequal_C','full_template_alignment_errors')):
            raise RuntimeError('TOKENIZER_ALIGNMENT_DRIFT '+model)
        if row.get('B_canonical_token_trie',{}).get('canonical_outputs')!=256:
            raise RuntimeError('TOKENIZER_GRAMMAR_DRIFT '+model)
        ls=row.get('candidate_token_lengths')
        if not isinstance(ls,list) or len(ls)!=8 or any(type(x) is not int or x<=0 for x in ls) or len(set(ls))!=1:
            raise RuntimeError('TOKENIZER_CANDIDATE_LENGTH_DRIFT '+model)
        if any(type(row.get(k)) is not int or row[k]<=0 or row[k]>=8192 for k in ('max_tokens_B','max_tokens_C')):
            raise RuntimeError('TOKENIZER_CONTEXT_DRIFT '+model)
    return True

def freeze_identity(root,cfg,m):
    root=Path(root)
    critical=['v22core/core.py','v22core/scoring.py','v22core/constraints.py',
       'v22core/tokenizer_gate.py','v22core/gpu_handoff.py',
       'protocol/V22_CORE_PROTOCOL_AMENDMENT.md',
       'protocol/V221_FREEZE_AMENDMENT.md']
    return {'study':'ThreatStudy-v2.2.1','baseline_archive_sha256':sha_file(root/ARCHIVE),
            'dataset_sha256':m['dataset_sha256'],'input_sha256':m['input_sha256'],
            'model_revisions':cfg['models'],'precision':['bf16','nf4'],
            'arm_order':['replay','C','B'],'critical_source_sha256':{s:sha_file(root/s) for s in critical},
            'replication_manifest_sha256':sha_file(root/'results/v22_replication_manifest.json'),
            'candidate_scoring':'serial_unormalized_includes_end_of_turn',
            'schema_language':'256_ascending_canonical_subsets',
            'seed':20261113}

def write_atomic(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.part')
    with tmp.open('w',encoding='utf-8') as f:
        json.dump(obj,f,sort_keys=True,indent=2,ensure_ascii=False)
        f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def authorization(root):
    root=Path(root);cfg,m,_,_,_=base(root,validate_records=False)
    file=root/RUNS/'authorization.json'
    if not file.exists():raise RuntimeError('V221_AUTHORIZATION_MISSING')
    a=json.loads(file.read_text())
    if a.get('status')!='V221_DATASET_BOUND_CPU_AUTHORIZATION' or a.get('authorization_sha256')!=digest({k:v for k,v in a.items() if k!='authorization_sha256'}):
        raise RuntimeError('V221_AUTHORIZATION_TAMPER')
    if a.get('freeze_identity')!=freeze_identity(root,cfg,m):
        raise RuntimeError('V221_AUTHORIZATION_DRIFT')
    gate_path=root/RUNS/'tokenizer_gate_v221.json'
    if not gate_path.exists() or sha_file(gate_path)!=a.get('tokenizer_gate_sha256'):
        raise RuntimeError('V221_TOKENIZER_GATE_FILE_DRIFT')
    validate_gate(json.loads(gate_path.read_text()),cfg,m)
    return a

def authorize(root,gate_path):
    root=Path(root);cfg,m,ws,_,baseline_audit=base(root,validate_records=True)
    input_path=Path(gate_path)
    if not input_path.is_file():raise RuntimeError('TOKENIZER_GATE_FILE_REQUIRED')
    data=json.loads(input_path.read_text());validate_gate(data,cfg,m)
    rec={'status':'V221_DATASET_BOUND_CPU_AUTHORIZATION',
       'freeze_identity':freeze_identity(root,cfg,m),
       'baseline_checkpoint_count':baseline_audit['checkpoints_verified'],
       'tokenizer_gate_sha256':sha_file(input_path),
       'caveat':'CPU authorization only; pinned GPU environment and real output integrity still must be validated.'}
    rec['authorization_sha256']=digest(rec)
    # Preserve a private, dataset-bound gate copy in the new run directory.
    dest=root/RUNS/'tokenizer_gate_v221.json'
    if dest.is_file() and sha_file(dest)!=sha_file(input_path):
        raise RuntimeError('EXISTING_GATE_PROVENANCE_DRIFT')
    write_atomic(dest,data)
    if sha_file(dest)!=sha_file(input_path):
        # Normalize only if original JSON differs in formatting; permit exact semantic copy
        dest.write_bytes(input_path.read_bytes())
    if (root/RUNS/'authorization.json').is_file():
        old=authorization(root)
        if old!=rec:raise RuntimeError('REAUTHORIZATION_DIFFERS_FROM_FROZEN')
    else:write_atomic(root/RUNS/'authorization.json',rec)
    authorization(root)
    return rec

def slug(model):return model.split('/')[-1].lower().replace('.','-')

def cell_dir(root,arm,model,precision):
    if arm not in ('replay','B','C'):raise ValueError('INVALID_ARM')
    return Path(root)/RUNS/'runs'/arm/slug(model)/precision

def record_path(root,arm,model,precision,window,anchor):
    return cell_dir(root,arm,model,precision)/f'example_{anchor}'/(window+'.json')

def rec_hash(rec):return digest({k:v for k,v in rec.items() if k!='record_sha256'})

def verify_rec(rec,identity,window,k,model,precision,arm):
    expected={'arm':arm,'model':model,'precision':precision,'anchor':k,
              'window_id':window['window_id'],'input_sha256':window['input_sha256'],
              'revision':identity['model_revision'],'identity_sha256':digest(identity),
              'prompt_sha256':digest([SYS_SINGLE if arm=='C' else SYS,prompt(window,k),model])}
    for key,expect in expected.items():
        if rec.get(key)!=expect:raise RuntimeError('V221_CHECKPOINT_IDENTITY_DRIFT '+key)
    if rec.get('record_sha256')!=rec_hash(rec):raise RuntimeError('V221_CHECKPOINT_HASH_TAMPER')
    if arm=='C':
        if len(rec.get('scores',[]))!=8 or len(rec.get('probability_mass',[]))!=8:
            raise RuntimeError('V221_C_SCORES_INCOMPLETE')
        if any(not math.isfinite(x) for x in rec['scores']) or any(not math.isfinite(x) for x in rec['probability_mass']):
            raise RuntimeError('V221_C_SCORES_NONFINITE')
        if not math.isclose(sum(rec['probability_mass']),1.,abs_tol=1e-8):raise RuntimeError('V221_C_MASS_INCOMPLETE')
        decided=argmax_lowest(rec['scores'])
        if rec['indices']!=[decided['index']] or rec.get('exact_ties')!=decided['exact_ties']:
            raise RuntimeError('V221_C_WINNER_DRIFT')
        if any(abs(a-b)>1e-8 for a,b in zip(rec['probability_mass'],softmax(rec['scores']))):
            raise RuntimeError('V221_C_PROBABILITY_MASS_DRIFT')
        if rec.get('valid') is not True:raise RuntimeError('V221_C_NOT_VALID')
    else:
        if rec.get('raw_sha256')!=digest(rec.get('raw')):raise RuntimeError('V221_RAW_HASH_TAMPER')
        p=parse(rec['raw'])
        if (rec['valid'],rec['indices'])!=(p['valid'],p['indices']):
            raise RuntimeError('V221_PARSER_DRIFT')
        if arm=='B' and (not p['valid'] or rec['raw'] not in canonical_language()):
            raise RuntimeError('V221_B_NONCANONICAL_OUTPUT')
    return rec

def cell_identity(root,arm,model,precision,cfg,m):
    return {'authorization_sha256':authorization(root)['authorization_sha256'],
          'arm':arm,'model':model,'model_revision':cfg['models'][model],
          'precision':precision,'baseline_input_sha256':m['input_sha256'],
          'bf16_dtype':'torch.bfloat16','attention':'sdpa',
          'quantization':('bitsandbytes NF4 4bit, double-quant disabled' if precision=='nf4' else 'native BF16'),
          'scoring':('serial teacher-forced sum including verified end-of-turn' if arm=='C' else 'greedy generation'),
          'max_new_tokens':96 if arm!='C' else None,
          'grammar':('256 ascending canonical JSON outputs' if arm=='B' else None)}

def load_model(model_name,revision,precision):
    import torch,transformers,bitsandbytes
    from transformers import AutoModelForCausalLM,AutoTokenizer,BitsAndBytesConfig
    if not torch.cuda.is_available():raise RuntimeError('CUDA_NOT_AVAILABLE')
    if torch.cuda.get_device_properties(0).total_memory < 20_000_000_000:
        raise RuntimeError('INSUFFICIENT_GPU_MEMORY')
    tok=AutoTokenizer.from_pretrained(model_name,revision=revision,use_fast=True,trust_remote_code=False)
    kw=dict(revision=revision,trust_remote_code=False,device_map={'':0},
        dtype=torch.bfloat16,attn_implementation='sdpa',low_cpu_mem_usage=True)
    if precision=='nf4':
        kw['quantization_config']=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',
             bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_use_double_quant=False)
    model=AutoModelForCausalLM.from_pretrained(model_name,**kw).eval()
    if any(p.device.type!='cuda' for p in model.parameters()):raise RuntimeError('CPU_OFFLOAD_DETECTED')
    env={'torch':torch.__version__,'transformers':transformers.__version__,
         'bitsandbytes':bitsandbytes.__version__,'cuda':torch.version.cuda,
         'gpu':torch.cuda.get_device_name(0),'revision':revision,'dtype':'bf16',
         'device_map':'cuda:0'}
    return model,tok,env

def calculate_output(model,tok,window,k,arm,model_name,max_input_tokens=8192):
    import torch
    system=SYS if arm!='C' else SYS_SINGLE
    message=model_messages(model_name,prompt(window,k),system)
    ids=apply_chat(tok,message,True)
    if len(ids)>max_input_tokens:raise RuntimeError('PROMPT_CONTEXT_TOO_LONG')
    tensor=torch.tensor([ids],dtype=torch.long,device='cuda:0')
    limit=getattr(model.config,'max_position_embeddings',None)
    if isinstance(limit,int) and len(ids)+96>limit:raise RuntimeError('MODEL_CONTEXT_LIMIT')
    torch.cuda.synchronize();start=time.perf_counter()
    with torch.inference_mode():
        if arm=='C':
            cands=encode_continuations(tok,model_name)
            r=score_candidates_serial(model,tensor,cands)
            response={'raw':None,'raw_sha256':None,'indices':[r['winner']],
              'valid':True,'scores':r['scores'],'probability_mass':r['probability_mass'],
              'candidate_token_lengths':r['candidate_token_lengths'],
              'exact_ties':r['exact_ties'],'end_marker_id':cands[0][-1],
              'generated_tokens':None,'cap_reached':None}
        else:
            kw={'do_sample':False,'num_beams':1,'max_new_tokens':96,
                'use_cache':True,'pad_token_id':tok.eos_token_id}
            if arm=='B':
                mark=tok.convert_tokens_to_ids(END_MARKER[model_name])
                trie=TokenTrie(lambda s:tok.encode(s,add_special_tokens=False),
                     lambda x:tok.decode(x,skip_special_tokens=True,clean_up_tokenization_spaces=False),mark)
                def allowed(batch_id,input_ids):
                    generated=input_ids[len(ids):].tolist()
                    options=trie.allowed(generated)
                    if not options:raise RuntimeError('NO_VALID_GRAMMAR_CONTINUATION')
                    return list(options)
                kw.update(prefix_allowed_tokens_fn=allowed,eos_token_id=mark)
            tokens=model.generate(input_ids=tensor,**kw)[0,len(ids):].tolist()
            # Arm A replay uses the exact v2.1.6 decoding call.
            # Arm B uses clean canonical output with no cleanup transformation.
            raw=(tok.decode(tokens,skip_special_tokens=True) if arm=='replay' else
                 tok.decode(tokens,skip_special_tokens=True,clean_up_tokenization_spaces=False))
            p=parse(raw)
            if arm=='B' and (not trie.accepts(tokens) or raw not in canonical_language()):
                raise RuntimeError('ARM_B_GRAMMAR_VIOLATION')
            response={'raw':raw,'raw_sha256':digest(raw),
                'indices':p['indices'],'valid':p['valid'],
                'generated_tokens':len(tokens),'cap_reached':len(tokens)>=96}
    torch.cuda.synchronize()
    response['latency_seconds']=round(time.perf_counter()-start,5)
    response['input_tokens']=len(ids)
    return response

def run_cell(root,arm,model_name,precision):
    import gc
    root=Path(root);auth=authorization(root)
    cfg,m,windows,_,_=base(root,validate_records=False)
    if model_name not in cfg['models'] or precision not in cfg['precisions'] or arm not in ('replay','B','C'):
        raise RuntimeError('INVALID_RUN_CELL')
    if arm=='replay':
        manifest=json.loads((root/'results/v22_replication_manifest.json').read_text())
        win_ids={x['window_id'] for x in manifest['selected_windows']}
        windows=[w for w in windows if w['window_id'] in win_ids]
        if len(windows)!=9:raise RuntimeError('REPLAY_WINDOW_SELECTION_DRIFT')
    ident=cell_identity(root,arm,model_name,precision,cfg,m)
    cdir=cell_dir(root,arm,model_name,precision)
    meta=cdir/'identity.json';env_file=cdir/'environment.json'
    if meta.is_file() and json.loads(meta.read_text())!=ident:
        raise RuntimeError('EXISTING_CELL_IDENTITY_DRIFT')
    if not meta.is_file() and any(cdir.rglob('example_*/*.json')):
        raise RuntimeError('ORPHAN_CHECKPOINT')
    count=0;remaining=[]
    for w in windows:
        for k in range(8):
            fp=record_path(root,arm,model_name,precision,w['window_id'],k)
            if fp.is_file():
                verify_rec(json.loads(fp.read_text()),ident,w,k,model_name,precision,arm)
                count+=1
            else:remaining.append((w,k))
    if not remaining:
        print('V221_CELL_COMPLETE',arm,model_name,precision,count,flush=True)
        return
    import random,torch
    random.seed(cfg['seed']);torch.manual_seed(cfg['seed']);torch.cuda.manual_seed_all(cfg['seed'])
    model,tok,env=load_model(model_name,cfg['models'][model_name],precision)
    if env_file.is_file() and json.loads(env_file.read_text())!=env:
        raise RuntimeError('GPU_PACKAGE_ENVIRONMENT_CHANGED')
    lock_path=root/RUNS/'runtime_lock.json'
    common={k:env[k] for k in ('torch','transformers','bitsandbytes','cuda','gpu')}
    if lock_path.is_file() and json.loads(lock_path.read_text())!=common:
        raise RuntimeError('CROSS_CELL_GPU_ENVIRONMENT_DRIFT')
    if not lock_path.is_file():write_atomic(lock_path,common)
    if not meta.is_file():write_atomic(meta,ident)
    if not env_file.is_file():write_atomic(env_file,env)
    try:
        archived={}
        if arm=='replay':
            with zipfile.ZipFile(root/ARCHIVE) as z:
                from .replay import cell_id
                stem='outputs/runs/'+cell_id(model_name,precision)
                for w in windows:
                    for k in range(8):
                        ap=f'{stem}/example_{k}/{w["window_id"]}.json'
                        archived[(w['window_id'],k)]=json.loads(z.read(ap))
        for w,k in remaining:
            result=calculate_output(model,tok,w,k,arm,model_name)
            rec={'arm':arm,'model':model_name,'precision':precision,
                'revision':cfg['models'][model_name],
                'window_id':w['window_id'],'report_id':w['report_id'],
                'source':w['source'],'anchor':k,'input_sha256':w['input_sha256'],
                'identity_sha256':digest(ident),'prompt_sha256':digest([SYS if arm!='C' else SYS_SINGLE,prompt(w,k),model_name]),
                **result}
            if arm=='replay':
                old=archived[(w['window_id'],k)]
                rec.update({'baseline_record_sha256':old['record_sha256'],
                   'byte_identical':old['raw']==rec['raw'],
                   'decision_identical':old['indices']==rec['indices'],
                   'validity_identical':old['valid']==rec['valid']})
            rec['record_sha256']=rec_hash(rec)
            verify_rec(rec,ident,w,k,model_name,precision,arm)
            write_atomic(record_path(root,arm,model_name,precision,w['window_id'],k),rec)
            count+=1
            print('V221_EVAL',arm,model_name,precision,f'{count}/{len(windows)*8}',flush=True)
    finally:
        del model,tok;gc.collect();torch.cuda.empty_cache()

def audit(root,allow_partial=False):
    root=Path(root);authorization(root)
    cfg,m,windows,_,_=base(root,validate_records=False)
    selection=json.loads((root/'results/v22_replication_manifest.json').read_text())
    replay_ids={w['window_id'] for w in selection['selected_windows']}
    replay_expect={(x['model'],x['precision'],x['window_id'],x['anchor']):x
                   for x in selection['calls']}
    if len(replay_expect)!=432:raise RuntimeError('REPLAY_MANIFEST_INCOMPLETE')
    rows={};cell_stats=[]
    for arm in ('replay','C','B'):
        applicable=[w for w in windows if arm!='replay' or w['window_id'] in replay_ids]
        for model in cfg['models']:
            for precision in cfg['precisions']:
                ident=cell_identity(root,arm,model,precision,cfg,m)
                expected=len(applicable)*8;count=0;byte=0;decision=0
                for w in applicable:
                    for k in range(8):
                        fp=record_path(root,arm,model,precision,w['window_id'],k)
                        if not fp.is_file():continue
                        rec=verify_rec(json.loads(fp.read_text()),ident,w,k,model,precision,arm)
                        rows[(arm,model,precision,w['window_id'],k)]=rec
                        count+=1
                        if arm=='replay':
                            check=replay_expect[(model,precision,w['window_id'],k)]
                            if rec.get('baseline_record_sha256')!=check['archived_record_sha256']:
                                raise RuntimeError('REPLAY_BASELINE_HASH_DRIFT')
                            if rec['byte_identical'] != (rec['raw_sha256']==check['archived_raw_sha256']):
                                raise RuntimeError('REPLAY_BYTE_COMPARISON_DRIFT')
                            if rec['decision_identical'] != (rec['indices']==check['archived_indices']):
                                raise RuntimeError('REPLAY_DECISION_COMPARISON_DRIFT')
                            if rec['validity_identical'] != (rec['valid']==check['archived_valid']):
                                raise RuntimeError('REPLAY_VALIDITY_COMPARISON_DRIFT')
                            byte+=int(rec['byte_identical']);decision+=int(rec['decision_identical'])
                cdir=cell_dir(root,arm,model,precision)
                extra=[p for p in cdir.glob('example_*/*.json') if p.stem not in {w['window_id'] for w in applicable}]
                if extra:raise RuntimeError('UNDECLARED_CHECKPOINT_FILES')
                cell_stats.append({'arm':arm,'model':model,'precision':precision,'count':count,'expected':expected,
                     'byte_identical':byte if arm=='replay' else None,
                     'decision_identical':decision if arm=='replay' else None})
    complete=all(r['count']==r['expected'] for r in cell_stats)
    if not complete and not allow_partial:raise RuntimeError('V221_GPU_MATRIX_INCOMPLETE')
    summaries=[]
    if complete:
        for arm in ('B','C'):
            raw_p={};temporary=[]
            for model in cfg['models']:
                bysource=collections.defaultdict(lambda:collections.defaultdict(list))
                for w in windows:
                    by_precision={}
                    for precision in ('bf16','nf4'):
                        pred={k:set(rows[(arm,model,precision,w['window_id'],k)]['indices']) for k in range(8)}
                        by_precision[precision]=original_effect(pred)['effect']
                    bysource[w['source']][w['report_id']].append(by_precision['nf4']-by_precision['bf16'])
                srcvals={s:sum(sum(v)/len(v) for v in r.values())/len(r) for s,r in bysource.items()}
                if len(srcvals)!=9 or any(len(r)!=8 for r in bysource.values()):
                    raise RuntimeError('SOURCE_CLUSTER_MISSING')
                p=exact_p(srcvals.values());delta=sum(srcvals.values())/9
                raw_p[model]=p;temporary.append({'arm':arm,'model':model,'delta':delta,'p_exact':p,'publisher_effects':srcvals})
            adjusted=holm(raw_p)
            for row in temporary:
                row['p_holm_within_arm']=adjusted[row['model']]
                summaries.append(row)
    out={'status':'V221_FULL_MATRIX_PASS' if complete else 'V221_PARTIAL_CHECKPOINT_AUDIT',
         'cells':cell_stats,'records_verified':len(rows),
         'mechanism_results':summaries,'caveat':'v2.2 arms B/C not registered on OSF by this software; results require interpretation.'}
    write_atomic(root/RUNS/'audit_summary.json',out)
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['authorize','verify','run','audit','status'])
    p.add_argument('--root',default='.')
    p.add_argument('--tokenizer-gate')
    p.add_argument('--arm',choices=['replay','B','C'])
    p.add_argument('--model');p.add_argument('--precision',choices=['bf16','nf4'])
    a=p.parse_args()
    if a.action=='authorize':
        if not a.tokenizer_gate:raise ValueError('--tokenizer-gate required')
        doc=authorize(a.root,a.tokenizer_gate)
        print('V221_DATASET_BOUND_CPU_AUTHORIZATION',doc['authorization_sha256'])
    elif a.action=='verify':
        auth=authorization(a.root);print('V221_CPU_AUTHORIZATION_VERIFIED',auth['authorization_sha256'])
    elif a.action=='run':
        if not all((a.arm,a.model,a.precision)):raise ValueError('--arm --model --precision required')
        run_cell(a.root,a.arm,a.model,a.precision)
    else:
        r=audit(a.root,allow_partial=a.action=='status')
        print(json.dumps(r,indent=2))

if __name__=='__main__':main()
