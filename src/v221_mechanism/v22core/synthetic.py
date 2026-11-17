"""v2.2-Core full-grid CPU integration test; NO LLM inference is performed."""
from __future__ import annotations
import argparse,collections,json,math,random
from pathlib import Path
from .core import SYS,SYS_SINGLE,prompt,parse,digest,original_effect,exact_p,holm
from .constraints import canonical
from .scoring import softmax,argmax_lowest
from .replay import validate_archive

N_ARMS=('B_schema','C_single_choice')

def generated_records(windows,models,cfg,m):
    for ix,w in enumerate(windows):
        base=(ix*3+1)%8
        for model,revision in models.items():
            for prec in ('bf16','nf4'):
                for k in range(8):
                    for arm in N_ARMS:
                        copied=(prec=='nf4' and ix%2==0)
                        selected=[k] if copied else [base]
                        rec={'synthetic_only':True,'arm':arm,'model':model,'revision':revision,
                             'precision':prec,'window_id':w['window_id'],
                             'input_sha256':w['input_sha256'],'anchor':k,
                             'protocol':'ThreatStudy-v2.2-CPU-SYNTHETIC-NOT-INFERENCE',
                             'source':w['source'],'report_id':w['report_id'],
                             'prompt_sha256':digest([SYS if arm=='B_schema' else SYS_SINGLE,prompt(w,k),model]),
                             'dataset_sha256':m['dataset_sha256']}
                        if arm=='B_schema':
                            rec.update({'raw':canonical(selected),'indices':selected,'valid':True})
                            rec['raw_sha256']=digest(rec['raw'])
                        else:
                            sc=[-2.0]*8;sc[selected[0]]=2.0
                            rec.update({'indices':selected,'candidate_log_probs':sc,
                                'candidate_softmax':softmax(sc),'exact_ties':1})
                        rec['record_sha256']=digest(rec)
                        yield rec

def verify_record(r,window,cfg,m):
    if not r.get('synthetic_only') or r['arm'] not in N_ARMS:raise RuntimeError('SYNTHETIC_MARKER_REQUIRED')
    if r['model'] not in cfg['models'] or r['revision']!=cfg['models'][r['model']]:raise RuntimeError('MODEL_ID_DRIFT')
    if r['window_id']!=window['window_id'] or r['input_sha256']!=window['input_sha256']:
        raise RuntimeError('WINDOW_ID_DRIFT')
    if r['dataset_sha256']!=m['dataset_sha256']:raise RuntimeError('DATASET_ID_DRIFT')
    if r['prompt_sha256']!=digest([SYS if r['arm']=='B_schema' else SYS_SINGLE,
                                    prompt(window,r['anchor']),r['model']]):raise RuntimeError('PROMPT_ID_DRIFT')
    if r['record_sha256']!=digest({k:v for k,v in r.items() if k!='record_sha256'}):
        raise RuntimeError('RECORD_TAMPER')
    if r['arm']=='B_schema':
        if r['raw_sha256']!=digest(r['raw']) or parse(r['raw'])['indices']!=r['indices'] or not parse(r['raw'])['valid']:
            raise RuntimeError('B_PARSER_DRIFT')
    else:
        score=argmax_lowest(r['candidate_log_probs'])
        if r['indices']!=[score['index']] or r['exact_ties']!=score['exact_ties']:
            raise RuntimeError('C_SCORING_DRIFT')
        if any(abs(a-b)>1e-12 for a,b in zip(softmax(r['candidate_log_probs']),r['candidate_softmax'])):
            raise RuntimeError('C_MASS_DRIFT')

def evaluate(records,windows,cfg,m):
    w_by={w['window_id']:w for w in windows};indexed={}
    for r in records:
        w=w_by[r['window_id']]
        verify_record(r,w,cfg,m)
        key=(r['arm'],r['model'],r['precision'],r['window_id'],r['anchor'])
        if key in indexed:raise RuntimeError('DUPLICATE_CHECKPOINT')
        indexed[key]=r
    needed=len(windows)*len(cfg['models'])*2*8*2
    if len(indexed)!=needed:raise RuntimeError('INCOMPLETE_SYNTHETIC_MATRIX '+str(len(indexed)))
    results=[]
    for arm in N_ARMS:
        per=[]
        for model in cfg['models']:
            groups=collections.defaultdict(lambda:collections.defaultdict(list))
            for w in windows:
                d={}
                for prec in ('bf16','nf4'):
                    pred={k:set(indexed[(arm,model,prec,w['window_id'],k)]['indices']) for k in range(8)}
                    d[prec]=original_effect(pred)['effect']
                groups[w['source']][w['report_id']].append(d['nf4']-d['bf16'])
            sources={s:sum(sum(v)/len(v) for v in reports.values())/len(reports)
                     for s,reports in groups.items()}
            if len(sources)!=9:raise RuntimeError('SOURCE_MATRIX_INCOMPLETE')
            mean=sum(sources.values())/len(sources)
            results.append({'arm':arm,'model':model,'synthetic_interaction':mean,
                            'synthetic_p':exact_p(sources.values()),'publishers':len(sources)})
        pp=holm({r['model']:r['synthetic_p'] for r in results if r['arm']==arm})
        for r in results:
            if r['arm']==arm:r['synthetic_holm_p']=pp[r['model']]
    return {'status':'SYNTHETIC_GRID_PASS_NO_REAL_V22_MODEL_RESULTS',
            'synthetic_checkpoint_count':needed,'windows':len(windows),
            'warning':'All values are deliberately simulated and must never enter empirical results tables.',
            'model_results':results}

def run(archive,outdir):
    cfg,m,windows,_,audit=validate_archive(archive)
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    records=list(generated_records(windows,cfg['models'],cfg,m))
    result=evaluate(records,windows,cfg,m)
    with (outdir/'v22_synthetic_checkpoints.jsonl').open('w') as f:
        for r in records:f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
    (outdir/'v22_synthetic_results.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();print(json.dumps(run(a.archive,a.out),indent=2))
