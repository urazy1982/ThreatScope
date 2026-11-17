#!/usr/bin/env python3
"""Independent matched-arm contrasts and hierarchical source/report bootstrap."""
from pathlib import Path
from collections import defaultdict
import csv,io,json,zipfile,random,itertools,statistics
D=Path(__file__).resolve().parent
rows=[]
with zipfile.ZipFile(D/'baseline_v216.zip') as z:
    for r in csv.DictReader(io.StringIO(z.read('outputs/analysis/window_effects.csv').decode())):
        rows.append({'arm':'A','model':r['model'],'publisher':r['source'],'report':r['report_id'],'window':r['window_id'],'difference':float(r['interaction'])})
for r in csv.DictReader((D/'independent_window_effects.csv').open()):
    rows.append({'arm':r['arm'],'model':r['model'],'publisher':r['publisher'],'report':r['report'],'window':r['window'],'difference':float(r['difference'])})
dat=defaultdict(dict);series=set();srcs=set();reports=defaultdict(set)
for r in rows:
    key=(r['model'],r['publisher'],r['report'],r['window'])
    dat[key][r['arm']]=r['difference'];series.add(r['model']);srcs.add(r['publisher']);reports[r['publisher']].add(r['report'])
assert len(dat)==len(series)*144
assert all(set(r)=={'A','B','C'} for r in dat.values())
assert len(srcs)==9 and all(len(reports[s])==8 for s in srcs)
srcs=sorted(srcs)
report_keys={(m,s,r):[key for key in dat if key[:3]==(m,s,r)] for m in series for s in srcs for r in reports[s]}
assert all(len(keys)==2 for keys in report_keys.values())

def sign_p(xs):
    xs=list(xs);n=len(xs);a=abs(sum(xs));return sum(abs(sum(v*sign for v,sign in zip(xs,signs)))>=a-1e-12 for signs in itertools.product((-1,1),repeat=n))/2**n

def agg(m,fun):
    pub={}
    rep={}
    for s in srcs:
        v=[]
        for r in sorted(reports[s]):
            x=statistics.mean(fun(dat[k]) for k in report_keys[m,s,r]);rep[s,r]=x;v.append(x)
        pub[s]=statistics.mean(v)
    return pub,rep

def ci(rep,seed=221,n=10000):
    rand=random.Random(seed)
    rep_values=[[rep[s,r] for r in sorted(reports[s])] for s in srcs]
    draw=rand.randrange
    vals=[]
    for _ in range(n):
        total=0.
        for _ in range(9):
            arr=rep_values[draw(9)]
            total += sum(arr[draw(8)] for _ in range(8))/8
        vals.append(total/9)
    vals.sort()
    return [vals[int(0.025*n)],vals[int(0.975*n)]]

fun_map={'A':lambda a:a['A'],'B':lambda a:a['B'],'C':lambda a:a['C'],'B_minus_A':lambda a:a['B']-a['A'],'C_minus_A':lambda a:a['C']-a['A'],'C_minus_B':lambda a:a['C']-a['B']}
res=[]
for m in sorted(series):
    for i,(name,fun) in enumerate(fun_map.items()):
        ps,rep=agg(m,fun);x=statistics.mean(ps.values());pv=sign_p(ps.values());lower,upper=ci(rep,seed=221+33*i)
        res.append({'model':m,'contrast':name,'effect_pp':x*100,'p_exact':pv,'ci_lower_pp':100*lower,'ci_upper_pp':100*upper,'publishers_positive':sum(x>0 for x in ps.values()),'publishers_negative':sum(x<0 for x in ps.values())})
(D/'independent_arm_comparisons.json').write_text(json.dumps(res,indent=2)+'\n')
with (D/'independent_arm_comparisons.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(res[0]));writer.writeheader();writer.writerows(res)
for r in res:
 print(r['model'].split('/')[-1].replace('-Instruct',''),r['contrast'],f"{r['effect_pp']:+.3f} pp",f"exact p={r['p_exact']:.5f}",f"95% CI [{r['ci_lower_pp']:+.3f},{r['ci_upper_pp']:+.3f}]")
