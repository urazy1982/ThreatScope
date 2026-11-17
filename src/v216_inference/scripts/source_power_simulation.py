"""Illustrative source-level sign-flip power under synthetic normal publisher effects.

Not a model performance simulation; not data-derived. Standardized delta=mean/SD.
Bonferroni 0.05/3 is a conservative pre-specified 3-model reference.
"""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
import numpy as np

def simulate(n,draws,seed):
    rng=np.random.default_rng(seed)
    signs=np.array(list(itertools.product([-1,1],repeat=n)),dtype=np.float64)
    scenarios=[]
    for standardized_delta in (0,0.3,0.5,0.8,1.0,1.3):
        vals=rng.normal(loc=standardized_delta,scale=1.0,size=(draws,n))
        sums=vals.sum(axis=1)
        null=np.abs(vals@signs.T)
        p=(null>=np.abs(sums[:,None])-1e-10).mean(axis=1)
        scenarios.append({'delta_over_publisher_sd':standardized_delta,
                          'unadjusted_p_below_0_05':round(float(np.mean(p<=0.05)),4),
                          'conservative_three_test_p_below_0_01667':round(float(np.mean(p<=0.05/3)),4)})
    return {'simulation_only':True,'source_clusters':n,'draws_per_scenario':draws,
            'seed':seed,'assumption':'independent normal publisher-level effects, fixed mean and SD=1',
            'caveat':'Not empirical power, source selection or publisher-level exchangeability evidence',
            'scenarios':scenarios,'two_sided_minimum_exact_p':2/(2**n)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    args=p.parse_args();v=simulate(10,4000,20261113)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(v,indent=2)+'\n')
    print('SOURCE_POWER_SIMULATION_PASS',len(v['scenarios']),'scenarios')
    for s in v['scenarios']:print(s)
if __name__=='__main__':main()
