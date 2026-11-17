#!/usr/bin/env python3
"""E2 CPU reanalysis: historically aligned Arm C likelihood scoring vs exact-space greedy.

Requires complete BF16 and NF4 (144 windows x 8 anchors) in distinct folders.
Does not touch original inference outputs. Primary unit: nine publishers; p exploratory.
"""
import argparse,csv,hashlib,itertools,json,random,statistics,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vendor.e1_neutral_gpu import canonical,sha,verify_frozen_inputs
from vendor.v22core.core import original_effect, SYS_SINGLE, prompt, digest
from vendor.v22core.tokenizer_gate import model_messages
from scripts.e2_singleton_gpu import PROTOCOL_ID, identity_for


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)

def signflip(vals):
    t=abs(sum(vals));tol=1e-12
    return sum(abs(sum(s*v for s,v in zip(signs,vals)))>=t-tol for signs in itertools.product((-1,1),repeat=len(vals)))/2**len(vals)

def read_cell(folder,model,precision,windows,manifest,cfg,manifest_path):
    observed=json.loads((folder/'identity.json').read_text())
    expected=identity_for(manifest,cfg,model,precision,(manifest_path,ROOT/'scripts/e2_singleton_gpu.py'))
    if observed!=expected:
        raise RuntimeError('CELL_IDENTITY_INVALID '+str(folder))
    if observed.get('runner_source_sha256')!=hashlib.sha256((ROOT/'scripts/e2_singleton_gpu.py').read_bytes()).hexdigest():
        raise RuntimeError('RUNNER_CODE_DRIFT')
    expected_hash=sha(canonical(observed))
    by_window={}
    for w in windows:
        choices={}
        for anchor in range(8):
            p=folder/'windows'/w['window_id']/f'anchor_{anchor}.json'
            if not p.is_file():raise RuntimeError('MISSING_E2_CHECKPOINT '+str(p))
            r=json.loads(p.read_text(encoding='utf-8'))
            if r.get('identity_sha256')!=expected_hash or r.get('window_id')!=w['window_id'] or r.get('anchor')!=anchor or r.get('precision')!=precision or r.get('model')!=model or r.get('revision')!=cfg['models'][model] or r.get('source')!=w['source'] or r.get('report_id')!=w['report_id'] or r.get('input_sha256')!=w['input_sha256']:
                raise RuntimeError('E2_RECORD_IDENTITY_DRIFT '+str(p))
            if r.get('prompt_sha256')!=sha(canonical(model_messages(model,prompt(w,anchor),SYS_SINGLE))):
                raise RuntimeError('E2_RECORD_PROMPT_DRIFT '+str(p))
            if r.get('valid') is not True or not isinstance(r.get('generated_ids'),list):
                raise RuntimeError('E2_RECORD_INVALID_OUTPUT '+str(p))
            if r.get('record_sha256')!=sha(canonical({k:v for k,v in r.items() if k!='record_sha256'})) or r.get('raw_sha256')!=sha(r.get('raw','')):
                raise RuntimeError('E2_RECORD_HASH_DRIFT '+str(p))
            ix=r.get('selected_index')
            if type(ix)!=int or ix not in range(8) or r.get('raw')!='{"relevant":['+str(ix)+']}':
                raise RuntimeError('E2_RECORD_SELECTION_INVALID '+str(p))
            choices[anchor]=[ix]
        by_window[w['window_id']]={'D':original_effect(choices)['effect'], 'choices':{k:choices[k][0] for k in choices}}
    return by_window

def hierarchical_bootstrap(rows_by_pub,draws=4000,seed=20261114):
    rng=random.Random(seed);pubs=sorted(rows_by_pub);samps=[]
    for _ in range(draws):
        means=[]
        for pub in rng.choices(pubs,k=len(pubs)):
            reps=rows_by_pub[pub]
            chosen=rng.choices(reps,k=len(reps))
            means.append(statistics.mean(x['greedy_minus_scoring_DID_pp'] for x in chosen))
        samps.append(statistics.mean(means))
    samps.sort();return [samps[int(.025*(draws-1))],samps[int(.975*(draws-1))]]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--results',type=Path,required=True);ap.add_argument('--model',default='Qwen/Qwen2.5-3B-Instruct')
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    manifest,windows,cfg=verify_frozen_inputs(a.inputs,a.manifest,a.model)
    hist=list(csv.DictReader((ROOT/'reference/independent_window_effects.csv').open(encoding='utf-8',newline='')))
    h={r['window']:r for r in hist if r['arm']=='C' and r['model']==a.model}
    hist_winners=list(csv.DictReader((ROOT/'reference/archived_armC_6912_winners.csv').open(encoding='utf-8',newline='')))
    hchoice={(r['precision'],r['window_id'],int(r['anchor'])):r for r in hist_winners if r['model']==a.model}
    if len(hchoice)!=144*8*2:raise RuntimeError('HISTORICAL_ARM_C_ANCHOR_FRAME_INCOMPLETE')
    if len(h)!=144 or set(h)!={w['window_id'] for w in windows}:
        raise RuntimeError('ARCHIVED_ARM_C_WINDOW_FRAME_MISMATCH')
    slug={'Qwen/Qwen2.5-3B-Instruct':'qwen2.5-3b',
          'meta-llama/Llama-3.2-3B-Instruct':'llama-3.2-3b',
          'mistralai/Mistral-7B-Instruct-v0.3':'mistral-7b'}[a.model]
    observed={p:read_cell(a.results/slug/p,a.model,p,windows,manifest,cfg,a.manifest) for p in ('bf16','nf4')}
    win=[];pubdict=defaultdict(list)
    for w in windows:
        wid=w['window_id'];hr=h[wid]
        if (hr['publisher'],hr['report'])!=(w['source'],w['report_id']):
            raise RuntimeError('HISTORICAL_SOURCE_BINDING_DRIFT '+wid)
        dgb=observed['bf16'][wid]['D'];dgn=observed['nf4'][wid]['D']
        agreements={}
        for precision in ('bf16','nf4'):
            vals=[]
            for anchor in range(8):
                hist_rec=hchoice[precision,wid,anchor]
                if hist_rec['publisher']!=w['source'] or hist_rec['report_id']!=w['report_id'] or hist_rec['input_sha256']!=w['input_sha256']:
                    raise RuntimeError('HISTORICAL_ARM_C_ANCHOR_SOURCE_DRIFT '+wid)
                if hist_rec['prompt_sha256']!=digest([SYS_SINGLE,prompt(w,anchor),a.model]):
                    raise RuntimeError('HISTORICAL_ARM_C_ANCHOR_PROMPT_DRIFT '+wid)
                vals.append(observed[precision][wid]['choices'][anchor]==int(hist_rec['winner']))
            agreements[precision]=sum(vals)/8
        dsb=float(hr['bf16_D']);dsn=float(hr['nf4_D'])
        if abs((dsn-dsb)-float(hr['difference']))>1e-9:
            raise RuntimeError('HISTORICAL_ARM_C_ARITHMETIC_DRIFT')
        r={'model':a.model,'publisher':w['source'],'report_id':w['report_id'],'window_id':wid,
           'greedy_bf16_D':dgb,'greedy_nf4_D':dgn,'scoring_bf16_D':dsb,'scoring_nf4_D':dsn,
           'greedy_vs_scoring_agreement_bf16':agreements['bf16'],
           'greedy_vs_scoring_agreement_nf4':agreements['nf4'],
           'greedy_precision_delta_pp':100*(dgn-dgb),'scoring_precision_delta_pp':100*(dsn-dsb),
           'greedy_minus_scoring_DID_pp':100*((dgn-dgb)-(dsn-dsb))}
        win.append(r);pubdict[w['source']].append(r)
    pub=[]
    for source,rs in sorted(pubdict.items()):
        if len(rs)!=16 or len({x['report_id'] for x in rs})!=8:
            raise RuntimeError('PUBLISHER_WINDOW_REPORT_COUNTS_WRONG')
        pub.append({'model':a.model,'publisher':source,'windows':len(rs),
            'greedy_precision_delta_pp':statistics.mean(x['greedy_precision_delta_pp'] for x in rs),
            'scoring_precision_delta_pp':statistics.mean(x['scoring_precision_delta_pp'] for x in rs),
            'greedy_minus_scoring_DID_pp':statistics.mean(x['greedy_minus_scoring_DID_pp'] for x in rs),
            'greedy_vs_scoring_agreement_bf16':statistics.mean(x['greedy_vs_scoring_agreement_bf16'] for x in rs),
            'greedy_vs_scoring_agreement_nf4':statistics.mean(x['greedy_vs_scoring_agreement_nf4'] for x in rs)})
    d=[x['greedy_minus_scoring_DID_pp'] for x in pub]
    summary={'status':'E2_CONSTRAINED_GREEDY_VS_HISTORICAL_ARM_C_COMPLETE',
            'protocol':PROTOCOL_ID,'comparison':'matched historical Arm C instruction/prompt and eight singleton suffixes; constrained greedy vs whole-suffix likelihood scoring',
            'model':a.model,'windows':144,'publishers':9,'greedy_generations':2304,
            'scoring_precision_delta_pp_publisher_equal':statistics.mean(x['scoring_precision_delta_pp'] for x in pub),
            'greedy_precision_delta_pp_publisher_equal':statistics.mean(x['greedy_precision_delta_pp'] for x in pub),
            'difference_of_precision_deltas_pp':statistics.mean(d),
            'greedy_vs_scoring_agreement_bf16':statistics.mean(x['greedy_vs_scoring_agreement_bf16'] for x in win),
            'greedy_vs_scoring_agreement_nf4':statistics.mean(x['greedy_vs_scoring_agreement_nf4'] for x in win),
            'exact_signflip_p_exploratory':signflip(d),'positive_publishers':sum(x>0 for x in d),
            'negative_publishers':sum(x<0 for x in d),
            'descriptive_hierarchical_CI95_pp':hierarchical_bootstrap(pubdict),
            'signflip_assumptions':'requires publisher sign-exchangeability under null; nine clusters; exploratory',
            'causal_scope':'procedure search contrast with the same singleton output space; no proof of complete mediation or operational CTI accuracy',
            'source':'Frozen v1.0.0 archived Arm C per-window results + new E2 checkpoints'}
    a.out.mkdir(parents=True,exist_ok=True)
    write_csv(a.out/'E2_by_window.csv',win);write_csv(a.out/'E2_by_publisher.csv',pub)
    (a.out/'E2_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('E2_CPU_ANALYSIS_PASS',json.dumps(summary,indent=2))

if __name__=='__main__':main()
