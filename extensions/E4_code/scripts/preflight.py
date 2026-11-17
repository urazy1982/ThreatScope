import csv,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.e4_runner import load_frozen,sha_file,model_messages
from vendor.core import SYS,prompt
from scripts.audit_e4 import BASELINE_SHA
base=Path.home()/'threat-study'
inputs=base/'ThreatScope_E3_v0_3/inputs_E3_private.jsonl'
gate=Path('/mnt/h/ThreatScope/E3/v0_3/GATE.json')
config=Path(__file__).resolve().parents[1]/'reference_config.json'
baseline=base/'ThreatScope_E3_GPU_v0_4/results/reports/E3_decisions_textfree.csv'
for p in (inputs,gate,config,baseline):
    if not p.is_file():raise RuntimeError('REQUIRED_FILE_MISSING '+str(p))
ws,g,c=load_frozen(inputs,gate,config)
assert sha_file(baseline)==BASELINE_SHA,'E3_BASELINE_SHA_MISMATCH'
assert len(ws)==72 and len(c['models'])==2 and c['precisions']==['fp4']
with baseline.open(newline='',encoding='utf8') as f:
    rows=list(csv.DictReader(f))
assert len(rows)==3456
for m in c['models']:
    assert len([r for r in rows if r['model']==m and r['precision']=='nf4'])==576
    assert len([r for r in rows if r['model']==m and r['precision']=='bf16'])==576
for w in ws:
    for k in range(8):
        p=prompt(w,k)
        assert f'{{"relevant":[{k}]}}' in p
        assert len(model_messages('Qwen/Qwen2.5-3B-Instruct',p))==2
print('E4_CPU_PREFLIGHT_PASS 72 windows 2 models 1 FP4 precision 1152 planned calls; E3 baseline SHA verified')
