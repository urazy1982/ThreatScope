"""Source-level exact sign-flip inference on balanced 8-prompt interventions.

No gold labels are used or claimed. A completed report is the dependence unit;
a reporting organization is the primary inference unit.
"""
from __future__ import annotations
import argparse,collections,csv,itertools,json,random,math
from pathlib import Path
from .core import read,lines,digest,parse,cell_id,write

def write_csv(path,records):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not records:return
    fields=list(dict.fromkeys(k for x in records for k in x))
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)

def anchor_effect(rows):
    """Rows map anchor index to selected indices or invalid-as-empty.

    Matched within-window contrast of inclusion(k) under prompt k vs mean
    inclusion(k) under the 7 prompts j != k. All positions weighted equally.
    """
    if set(rows)!=set(range(8)):raise ValueError('INCOMPLETE_PROMPT_SET')
    return sum((int(k in rows[k])-sum(int(k in rows[j]) for j in range(8) if j!=k)/7)/8
               for k in range(8))

def effect_from_rows(rows,cardinality=False):
    return anchor_effect(rows)

def exact_sign_flip(vals):
    vals=list(vals);n=len(vals)
    if n<2:raise ValueError('TOO_FEW_SOURCES')
    observed=abs(sum(vals)/n)
    ge=0
    for signs in itertools.product((-1,1),repeat=n):
        x=abs(sum(a*s for a,s in zip(vals,signs))/n)
        if x>=observed-1e-12:ge+=1
    return ge/(2**n)

def cluster_bootstrap(source_reports,seed,draws):
    """Hierarchical source-then-report bootstrap; cannot replace source exact p."""
    rng=random.Random(seed);src=list(sorted(source_reports));out=[]
    for _ in range(draws):
        batch=[]
        for s in (rng.choice(src) for _ in src):
            reports=source_reports[s]
            batch.append(sum(rng.choice(reports) for _ in reports)/len(reports))
        out.append(sum(batch)/len(batch))
    out.sort();return [out[int(.025*(len(out)-1))],out[int(.975*(len(out)-1))]]

def verify_prepared(root):
    root=Path(root);cfg=read(root/'config/study.json');m=read(root/'outputs/prepared/manifest.json')
    if m['protocol']!=cfg['protocol'] or m['config_sha256']!=__import__('hashlib').sha256((root/'config/study.json').read_bytes()).hexdigest():
        raise RuntimeError('PREPARED_CONFIG_DRIFT')
    data=(root/'outputs/prepared/inputs.jsonl').read_bytes()
    if digest(data)!=m['input_sha256']:raise RuntimeError('PREPARED_INPUT_DRIFT')
    windows=lines(root/'outputs/prepared/inputs.jsonl')
    if len(windows)!=m['windows'] or len(set(w['window_id'] for w in windows))!=len(windows):raise RuntimeError('WINDOWS_DRIFT')
    for w in windows:
        cp=dict(w);dh=cp.pop('input_sha256')
        if digest(cp)!=dh:raise RuntimeError('INPUT_SHA_MISMATCH')
    return cfg,m,windows

def load_results(root,verify=True):
    from .runner import validate_checkpoint
    cfg,m,windows=verify_prepared(root)
    records={};n_invalid=collections.Counter()
    for model,revision in cfg['models'].items():
        for precision in cfg['precisions']:
            base=Path(root)/'outputs/runs'/cell_id(model,precision)
            meta_path=base/'run_metadata.json'
            if not meta_path.exists():raise RuntimeError('MISSING_CELL_METADATA '+str(base))
            meta=read(meta_path)
            from .runner import expected_identity
            if meta!=expected_identity(root,model,precision):raise RuntimeError('CELL_IDENTITY_MISMATCH')
            for w in windows:
                for k in range(8):
                    path=base/f'example_{k}'/(w['window_id']+'.json')
                    if not path.exists():raise RuntimeError('MISSING_CHECKPOINT '+str(path))
                    rec=read(path)
                    if verify:validate_checkpoint(path,w,k,model,precision,revision,digest(meta))
                    records[(model,precision,w['window_id'],k)]=rec
                    n_invalid[(model,precision)]+=int(not rec['valid'])
            for k in range(8):
                d=base/f'example_{k}'
                if len(list(d.glob('*.json')))!=len(windows):raise RuntimeError('EXTRA_CHECKPOINTS '+str(d))
    return cfg,m,windows,records,n_invalid

def analyze(root):
    cfg,m,windows,records,invalid=load_results(root)
    out=Path(root)/'outputs/analysis';out.mkdir(parents=True,exist_ok=True)
    winrows=[];report={};source={};summary=[];sourcerows=[];all_models=[]
    for model in cfg['models']:
        data=collections.defaultdict(lambda:collections.defaultdict(list))
        for w in windows:
            per={}
            for precision in cfg['precisions']:
                r={k:records[(model,precision,w['window_id'],k)] for k in range(8)}
                chosen={k:(set(r[k]['indices']) if r[k]['valid'] else set()) for k in range(8)}
                effect=anchor_effect(chosen)
                valid_all=all(r[k]['valid'] for k in range(8))
                per[precision]=(effect,valid_all)
            delta=per['nf4'][0]-per['bf16'][0]
            winrows.append({'model':model,'source':w['source'],'report_id':w['report_id'],
                            'window_id':w['window_id'],'bf16_effect':per['bf16'][0],
                            'nf4_effect':per['nf4'][0],'interaction':delta,
                            'complete_valid_bf16':per['bf16'][1],
                            'complete_valid_nf4':per['nf4'][1]})
            data[w['source']][w['report_id']].append((delta,per['bf16'][0],per['nf4'][0],
                                                       per['bf16'][1] and per['nf4'][1]))
        groupmeans={};valid_groupmeans={};source_report_effects={};all_r=[]
        for s,rs in sorted(data.items()):
            values=[];valid_values=[]
            for rid,ww in sorted(rs.items()):
                d=sum(x[0] for x in ww)/len(ww)
                b=sum(x[1] for x in ww)/len(ww)
                q=sum(x[2] for x in ww)/len(ww)
                all_valid=all(x[3] for x in ww)
                report[(model,rid)]={'interaction':d,'bf16':b,'nf4':q,'source':s,'valid':all_valid}
                values.append(d);all_r.append(d)
                if all_valid:valid_values.append(d)
            groupmeans[s]=sum(values)/len(values)
            source_report_effects[s]=values
            if valid_values:valid_groupmeans[s]=sum(valid_values)/len(valid_values)
            sourcerows.append({'model':model,'source':s,'reports':len(values),'interaction':groupmeans[s],
                               'all_valid_reports':len(valid_values)})
        if set(groupmeans)!=set(cfg['source_names']):raise RuntimeError('MISSING_SOURCE_IN_ANALYSIS')
        effect=sum(groupmeans.values())/len(groupmeans)
        p=exact_sign_flip(groupmeans.values())
        ci=cluster_bootstrap(source_report_effects,cfg['seed'],cfg['report_bootstrap_draws'])
        # report-level estimate is descriptive, not a separate significance claim
        b=sum(v['bf16'] for (mo,rid),v in report.items() if mo==model)/len(all_r)
        q=sum(v['nf4'] for (mo,rid),v in report.items() if mo==model)/len(all_r)
        summary.append({'model':model,'source_groups':len(groupmeans),'reports':len(all_r),
                        'source_equal_interaction':effect,'bf16_report_mean_effect':b,
                        'nf4_report_mean_effect':q,'source_signflip_two_sided_p':p,
                        'hierarchical_bootstrap_ci_low':ci[0],
                        'hierarchical_bootstrap_ci_high':ci[1],
                        'invalid_bf16':invalid[(model,'bf16')],
                        'invalid_nf4':invalid[(model,'nf4')],
                        'all_valid_source_count':len(valid_groupmeans),
                        'valid_only_source_equal_interaction':(sum(valid_groupmeans.values())/len(valid_groupmeans) if len(valid_groupmeans)==len(groupmeans) else None)})
    # Holm for three prespecified models
    sorted_rows=sorted(summary,key=lambda r:r['source_signflip_two_sided_p'])
    biggest=0
    for i,row in enumerate(sorted_rows):
        biggest=max(biggest,min(1,(len(summary)-i)*row['source_signflip_two_sided_p']))
        row['holm_p']=biggest
    write_csv(out/'window_effects.csv',winrows)
    write_csv(out/'source_effects.csv',sourcerows if False else sourcerows)
    write_csv(out/'model_summary.csv',summary)
    result={'protocol':cfg['protocol'],'status':'COMPLETE','rows':len(windows)*8*len(cfg['models'])*len(cfg['precisions']),
            'no_gold_labels':True,'models':summary,'source_count':len(cfg['source_names']),
            'files_sha256':{p.name:__import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.csv'))}}
    write(out/'summary.json',result)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args()
    print(json.dumps(analyze(a.root),indent=2))
if __name__=='__main__':main()
