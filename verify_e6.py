#!/usr/bin/env python3
"""ThreatScope E6 integrated replay and basic text-free record audit, stdlib only."""
from pathlib import Path
from collections import Counter
import json,subprocess,sys,csv,hashlib
root=Path(__file__).resolve().parent
p=root/'extensions/E5_synthesis/verify_e5.py'
r=subprocess.run([sys.executable,str(p)],cwd=p.parent,capture_output=True,text=True)
print(r.stdout.strip())
if r.returncode:print(r.stderr,file=sys.stderr);sys.exit(r.returncode)
assert 'THREATSCOPE_E5_CROSS_STUDY_REPLAY_PASS' in r.stdout
for stage,expected in [('E3_checkpoints',3456),('E4_checkpoints',1152)]:
 paths=list((root/'extensions'/stage/'results').rglob('example_*/*.json'))
 assert len(paths)==expected,(stage,len(paths),expected)
 bad=0;valid=0
 for f in paths:
  obj=json.loads(f.read_text(encoding='utf-8'))
  if not isinstance(obj.get('valid'),bool) or not isinstance(obj.get('window_id'),str):bad+=1
  if obj.get('valid'):valid+=1
  if 'sentence_text' in obj or 'context_before' in obj:bad+=1
 assert not bad,(stage,bad)
 print('CHECKPOINT_PASS',stage,len(paths),'valid',valid)
for file,count in [('E1_window_decisions_1728.csv',1728),('E2_per_prompt_decisions_2304.csv',2304),('E3_decisions_textfree.csv',3456),('E4_decisions_textfree.csv',1152)]:
 p=root/'extensions/E5_synthesis/evidence'/file
 with p.open(newline='',encoding='utf-8') as fh:
  reader=csv.DictReader(fh);rows=list(reader)
 assert len(rows)==count,(file,len(rows))
 assert not {'sentence_text','context_before','report_text'}&set(reader.fieldnames),(file,reader.fieldnames)
 print('DECISION_TABLE_PASS',file,len(rows))
print('THREATSCOPE_E6_CPU_AUDIT_PASS')
