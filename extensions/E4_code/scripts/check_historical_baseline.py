"""CPU-only, text-free reproducibility test of historical E3 NF4-BF16 effects."""
import csv,json,sys,itertools
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.audit_e4 import D,BASELINE_SHA
from scripts.e4_runner import sha_file
EXPECTED={'Qwen/Qwen2.5-3B-Instruct':18.67,'meta-llama/Llama-3.2-3B-Instruct':5.27}
def run(path):
    if sha_file(path)!=BASELINE_SHA:raise RuntimeError('E3_BASELINE_SHA_MISMATCH')
    with open(path,newline='',encoding='utf8') as f: rows=list(csv.DictReader(f))
    assert len(rows)==3456
    matrix={}
    wm={}
    for r in rows:
        key=(r['model'],r['precision'],r['window_id'],int(r['anchor']))
        assert key not in matrix,'DUPLICATE E3 ROW'
        matrix[key]={'valid':r['valid']=='True','indices':json.loads(r['indices'])}
        wm[r['window_id']]=(r['source'],r['report_id'])
    sums={}
    for m in EXPECTED:
        values=defaultdict(list)
        for prec in ('bf16','nf4'):
            for wid,(pub,report) in wm.items():
                vals={k:matrix[(m,prec,wid,k)] for k in range(8)}
                values[(m,prec,pub)].append(D(vals))
        pubs=sorted({p for p,r in wm.values()})
        effect=sum(sum(values[(m,'nf4',p)])/len(values[(m,'nf4',p)]) - sum(values[(m,'bf16',p)])/len(values[(m,'bf16',p)]) for p in pubs)/len(pubs)*100
        print('E3_BASELINE_REPLAY',m,'NF4-BF16_pp',round(effect,6),'published_approx',EXPECTED[m])
        assert abs(effect-EXPECTED[m])<0.03,'E3_BASELINE_REPLAY_DISAGREES'
        sums[m]=effect
    print('E4_HISTORICAL_BASELINE_REPLAY_PASS')
    return sums
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: check_historical_baseline.py /path/to/E3_decisions_textfree.csv')
    run(Path(sys.argv[1]))
