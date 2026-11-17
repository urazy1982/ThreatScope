#!/usr/bin/env python3
"""Strict E4 FP4 checkpoint audit and matched E3 BF16/NF4 comparison."""
import argparse,csv,hashlib,itertools,json,math,sys
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.e4_runner import load_frozen, validate_checkpoint, sha_file, PROTOCOL
from vendor.core import digest,read
MODELS={'Qwen/Qwen2.5-3B-Instruct':'qwen2.5-3b-instruct','meta-llama/Llama-3.2-3B-Instruct':'llama-3.2-3b-instruct'}
BASELINE_SHA='e750458e3a91688601255d15a6507adeeeb8c54f48d803064f25af0559ba4d5f'

def D(recs):
    # Invalid output maps to no selection; frozen historical Arm A rule.
    assert len(recs)==8 and set(recs)==set(range(8))
    matched=sum(int(recs[k]['valid'] and k in recs[k]['indices']) for k in range(8))/8
    others=sum(int(recs[k]['valid'] and j in recs[k]['indices']) for k in range(8) for j in range(8) if j!=k)/56
    return matched-others

def effect_by_publisher(ws, rows, model, precision):
    recs={(r['window_id'],int(r['anchor'])):r for r in rows if r['model']==model and r['precision']==precision}
    by=defaultdict(list)
    for w in ws:
        items={k:recs[(w['window_id'],k)] for k in range(8)}
        by[w['source']].append(D(items))
    return {pub:sum(v)/len(v) for pub,v in by.items()}

def run(a):
    ws,gate,cfg=load_frozen(Path(a.inputs),Path(a.gate),Path(a.config))
    if sha_file(a.baseline)!=BASELINE_SHA:raise RuntimeError('E3_BASELINE_SHA_MISMATCH')
    with open(a.baseline,newline='',encoding='utf8') as f: baseline=list(csv.DictReader(f))
    all_models=set(MODELS)
    if len(baseline)!=3456:raise RuntimeError('E3_BASELINE_ROW_COUNT')
    if set(r['model'] for r in baseline)!=(all_models|{'mistralai/Mistral-7B-Instruct-v0.3'}):raise RuntimeError('E3_BASELINE_MODELS')
    if any(r['precision'] not in ('bf16','nf4') for r in baseline):raise RuntimeError('BAD_E3_BASELINE_PRECISION')
    # Verify full, unique baseline coverage for 3 models x 2 precision x 72 windows x 8 anchors.
    expected={(model,prec,w['window_id'],str(k)) for model in set(r['model'] for r in baseline) for prec in ('bf16','nf4') for w in ws for k in range(8)}
    observed={(r['model'],r['precision'],r['window_id'],r['anchor']) for r in baseline}
    if len(observed)!=len(baseline) or observed!=expected:raise RuntimeError('E3_BASELINE_GRID_DRIFT')
    wmap={w['window_id']:w for w in ws}
    for r in baseline:
        w=wmap[r['window_id']]
        if r['source']!=w['source'] or r['report_id']!=w['report_id'] or r['input_sha256']!=w['input_sha256']:
            raise RuntimeError('E3_BASELINE_IDENTITY_MISMATCH')
        r['valid']=str(r['valid']).strip().lower()=='true'
        r['indices']=json.loads(r['indices'])
        if not isinstance(r['indices'],list):raise RuntimeError('BAD_BASELINE_INDICES')
        if r['valid'] and (len(set(r['indices']))!=len(r['indices']) or any(type(i)!=int or i not in range(8) for i in r['indices'])):raise RuntimeError('BAD_BASELINE_SELECTION')
    fp4=[];status=[]
    for model,rev in cfg['models'].items():
        folder=Path(a.results)/MODELS[model]/'fp4'
        meta=folder/'run_metadata.json'
        if not meta.exists():raise RuntimeError('MISSING_E4_META '+str(meta))
        ident=read(meta)
        if ident.get('protocol')!=PROTOCOL or ident.get('model')!=model or ident.get('precision')!='fp4':raise RuntimeError('E4_METADATA_DRIFT')
        if ident.get('runner_sha256')!=sha_file(Path(__file__).parent/'e4_runner.py'):raise RuntimeError('E4_RUNNER_SHA_DRIFT')
        ih=digest(ident);good=0
        for w in ws:
            for k in range(8):
                p=folder/f'example_{k}'/(w['window_id']+'.json')
                if not p.exists():raise RuntimeError('E4_CHECKPOINT_MISSING '+str(p))
                r=validate_checkpoint(p,w,k,model,'fp4',rev,ih)
                good+=int(r['valid'])
                fp4.append({'model':model,'precision':'fp4','source':w['source'],'report_id':w['report_id'],'window_id':w['window_id'],'anchor':k,'valid':r['valid'],'indices':r['indices'],'input_sha256':w['input_sha256'],'record_sha256':r['record_sha256']})
        status.append({'model':model,'total':576,'valid':good,'invalid':576-good})
    rows=baseline+fp4
    publisher=[]
    for model in MODELS:
        effects={prec:effect_by_publisher(ws,rows,model,prec) for prec in ('bf16','nf4','fp4')}
        for pub in sorted(effects['bf16']):
            publisher.append({'model':model,'publisher':pub,'D_bf16':effects['bf16'][pub],'D_nf4':effects['nf4'][pub],'D_fp4':effects['fp4'][pub],'NF4_minus_BF16':effects['nf4'][pub]-effects['bf16'][pub],'FP4_minus_BF16':effects['fp4'][pub]-effects['bf16'][pub],'FP4_minus_NF4':effects['fp4'][pub]-effects['nf4'][pub]})
    results=[]
    for model in MODELS:
        pr=[r for r in publisher if r['model']==model]
        for contrast in ('NF4_minus_BF16','FP4_minus_BF16','FP4_minus_NF4'):
            v=[r[contrast] for r in pr];obs=sum(v)/len(v)
            ref=[abs(sum(x*s for x,s in zip(v,signs))/len(v)) for signs in itertools.product((-1,1),repeat=len(v))]
            p=sum(x>=abs(obs)-1e-12 for x in ref)/len(ref)
            results.append({'model':model,'contrast':contrast,'effect_pp':round(obs*100,8),'p_exploratory':p,'publishers':len(v),'positive':sum(x>1e-12 for x in v),'negative':sum(x< -1e-12 for x in v),'tied':sum(abs(x)<=1e-12 for x in v)})
    # Primary family: FP4 minus NF4 interaction across two model families (Holm-2).
    primary=sorted([r for r in results if r['contrast']=='FP4_minus_NF4'],key=lambda x:x['p_exploratory'])
    running=0.0
    for i,r in enumerate(primary):
        running=max(running, min(1.0,(len(primary)-i)*r['p_exploratory']))
        r['holm2_primary_p']=running
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    with (out/'E4_decisions_textfree.csv').open('w',newline='',encoding='utf8') as f:
        wr=csv.DictWriter(f,fieldnames=list(fp4[0]));wr.writeheader();wr.writerows([{**r,'indices':json.dumps(r['indices'],separators=(',',':'))} for r in fp4])
    with (out/'E4_publisher_effects.csv').open('w',newline='',encoding='utf8') as f:
        wr=csv.DictWriter(f,fieldnames=list(publisher[0]));wr.writeheader();wr.writerows(publisher)
    report={'status':'PASS','protocol':PROTOCOL,'frozen_E3_sha256':gate['new_inputs_sha256'],'baseline_csv_sha256':BASELINE_SHA,'fp4_checkpoints':len(fp4),'cells':status,'effects':results,'note':'Retrospective same-archive E3 windows, exploratory, eight publisher sign flip; BF16/NF4 reused from E3.'}
    (out/'E4_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('E4_AUDIT_PASS',len(fp4),'FP4 checkpoints; baseline 3456 records; comparisons 6')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for x in ('inputs','gate','config','baseline','results','out'):p.add_argument('--'+x,required=True)
    run(p.parse_args())
