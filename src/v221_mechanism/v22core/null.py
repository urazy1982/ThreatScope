"""Exploratory cardinality-preserving index-exchangeability reference simulation.

Keep exactly the number of selected indices from EACH of the 6,912 v2.1.6
responses; randomly reassign their positions among 0..7, breaking link between
prompt example and selected index. This is a synthetic conditional reference
under a strong exchangeability assumption, not a causal or confirmatory test.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from .replay import validate_archive

def simulate(archive,draws=10000,seed=20261113,chunk=128):
    cfg,m,windows,rows,checks=validate_archive(archive)
    rng=np.random.default_rng(seed)
    results=[];N=len(windows)
    for model in cfg['models']:
        cards={};observed={}
        for precision in ('bf16','nf4'):
            arr=np.array([[len(rows[(model,precision,w['window_id'],e)]['indices']) for e in range(8)] for w in windows],dtype=np.int16)
            cards[precision]=arr
            observed[precision]=sum(e in rows[(model,precision,w['window_id'],e)]['indices'] for w in windows for e in range(8))
        Cdelta=(int(cards['nf4'].sum())-int(cards['bf16'].sum()))/8
        obs=(observed['nf4']-observed['bf16']-Cdelta)/(7*N)
        sims=[]
        for start in range(0,draws,chunk):
            count=min(chunk,draws-start)
            # Under uniform random subsets of c indices, the demonstrated index
            # is present with exact marginal probability c/8.
            tnf=(rng.random((count,N,8))<(cards['nf4'][None,:,:]/8)).sum(axis=(1,2))
            tbf=(rng.random((count,N,8))<(cards['bf16'][None,:,:]/8)).sum(axis=(1,2))
            sims.extend(((tnf-tbf-Cdelta)/(7*N)).tolist())
        sims=np.asarray(sims)
        p=(1+int((np.abs(sims)>=abs(obs)-1e-12).sum()))/(draws+1)
        results.append({'model':model,'observed_raw_interaction':float(obs),'draws':draws,'null_mean':float(sims.mean()),
            'null_standard_deviation':float(sims.std(ddof=1)),
            'null_central_95_interval':[float(np.quantile(sims,.025)),float(np.quantile(sims,.975))],
            'empirical_two_sided_tail_fraction':p,
            'interpretation':'Exploratory index-exchangeability reference, not a randomized experiment or evidence of mediation'})
    return {'status':'CARDINALITY_PRESERVING_REFERENCE_DONE','seed':seed,'draws_per_model':draws,'models':results}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True)
    p.add_argument('--draws',type=int,default=10000);a=p.parse_args()
    result=simulate(a.archive,a.draws)
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
