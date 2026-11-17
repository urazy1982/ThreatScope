#!/usr/bin/env python3
"""Independent, stdlib-only ThreatScope E4 text-free checkpoint and numerical audit."""
import csv,hashlib,io,itertools,json,math,statistics,sys,zipfile
from collections import Counter,defaultdict
from pathlib import Path
Z=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/ThreatScope_E4_Complete_Results.zip')
OUT=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/mnt/data/e4_independent_audit')
OUT.mkdir(parents=True,exist_ok=True)
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(o):return hashlib.sha256(canon(o)).hexdigest()
def loadcsv(z,name):
  path=next(n for n in z.namelist() if n.endswith('/'+name));return list(csv.DictReader(io.StringIO(z.read(path).decode('utf-8'))))
def loadjson(z,name):
  path=next(n for n in z.namelist() if n.endswith('/'+name));return json.loads(z.read(path))
def parse(raw):
 try:
  j=json.loads(raw.strip())
  if type(j)!=dict or set(j)!={'relevant'}:return False,[]
  a=j['relevant']
  if type(a)!=list or len(a)>8 or any(type(i)!=int or i not in range(8) for i in a) or len(set(a))!=len(a):return False,[]
  return True,sorted(a)
 except (TypeError,ValueError):return False,[]

def conv(row):return dict(model=row['model'],precision=row['precision'],source=row['source'],report_id=row['report_id'],window_id=row['window_id'],anchor=int(row['anchor']),valid=str(row['valid']).strip().lower()=='true',indices=json.loads(row['indices']),input_sha256=row['input_sha256'])
def D(rows):
 kset={r['anchor']:r for r in rows};assert len(rows)==8 and set(kset)==set(range(8))
 match=sum(int(kset[k]['valid'] and k in kset[k]['indices']) for k in range(8))/8
 other=sum(int(kset[k]['valid'] and j in kset[k]['indices']) for k in range(8) for j in range(8) if j!=k)/56
 return match-other
with zipfile.ZipFile(Z) as z:
 assert z.testzip() is None
 files=z.namelist();base=next(n.split('/')[0] for n in files if n.endswith('/PROTOCOL_FREEZE.md'))
 summary=loadjson(z,'E4_summary.json');baseline=[conv(r) for r in loadcsv(z,'E3_reference_decisions.csv')]
 export=[conv(r) for r in loadcsv(z,'E4_decisions_textfree.csv')]
 exported_raw=loadcsv(z,'E4_decisions_textfree.csv')
 meta={}
 for n in files:
  if n.endswith('/run_metadata.json'):
   d=json.loads(z.read(n));meta[d['model']]=d
 cp=[];fail=[]
 for n in files:
  if '/results/E4/' not in n or '/example_' not in n or not n.endswith('.json'):continue
  r=json.loads(z.read(n));ok=True
  if n.split('/')[-2]!=f"example_{r['anchor']}" or not n.endswith('/'+r['window_id']+'.json'):fail.append([n,'PATH'])
  if digest(r['raw'])!=r['raw_sha256']:fail.append([n,'RAW_HASH'])
  if digest({k:v for k,v in r.items() if k!='record_sha256'})!=r['record_sha256']:fail.append([n,'RECORD_HASH'])
  valid,indices=parse(r['raw'])
  if r['valid']!=valid or r['indices']!=indices:fail.append([n,'SCHEMA'])
  if r['precision']!='fp4':fail.append([n,'PRECISION'])
  if r['model'] not in meta:fail.append([n,'MISSING_META'])
  elif digest(meta[r['model']])!=r['identity_sha256']:fail.append([n,'IDENTITY'])
  cp.append(r)
 assert not fail,fail[:5]
 assert len(cp)==1152 and len(export)==1152 and len(baseline)==3456
 grid={(r['model'],r['precision'],r['window_id'],r['anchor']):r for r in baseline+export}
 assert len(grid)==4608
 for r in cp:
  key=(r['model'],'fp4',r['window_id'],r['anchor']);v=grid[key]
  assert (r['valid'],r['indices'],r['input_sha256'])==(v['valid'],v['indices'],v['input_sha256'])
  ex=next(x for x in exported_raw if (x['model'],x['window_id'],int(x['anchor']))==(r['model'],r['window_id'],r['anchor']))
  assert ex['record_sha256']==r['record_sha256']
 source_by_window={}
 for r in baseline+export:
  w=r['window_id'];value=(r['source'],r['report_id'],r['input_sha256'])
  assert w not in source_by_window or source_by_window[w]==value
  source_by_window[w]=value
 assert len(source_by_window)==72
 groups=defaultdict(list)
 for r in baseline+export:groups[(r['model'],r['precision'],r['source'],r['report_id'],r['window_id'])].append(r)
 assert all(len(v)==8 for v in groups.values())
 per=defaultdict(list)
 for (model,prec,source,report,window),rows in groups.items():per[(model,source,prec)].append(D(rows))
 pubrows=[];effectrows=[]
 for model in sorted({r['model'] for r in export}):
  publishers=sorted({p for m,p,q in per if m==model})
  assert len(publishers)==8
  pubvals={}
  for p in publishers:
   d={q:statistics.mean(per[(model,p,q)]) for q in ('bf16','nf4','fp4')}
   pubvals[p]=d
   pubrows.append({'model':model,'publisher':p,**{'D_'+q:d[q] for q in d},'NF4_minus_BF16':d['nf4']-d['bf16'],'FP4_minus_BF16':d['fp4']-d['bf16'],'FP4_minus_NF4':d['fp4']-d['nf4']})
  for contrast,a,b in [('NF4_minus_BF16','nf4','bf16'),('FP4_minus_BF16','fp4','bf16'),('FP4_minus_NF4','fp4','nf4')]:
   v=[pubvals[p][a]-pubvals[p][b] for p in publishers]
   t=statistics.mean(v)
   null=[abs(statistics.mean([x*s for x,s in zip(v,sign)])) for sign in itertools.product((-1,1),repeat=8)]
   pval=sum(x>=abs(t)-1e-12 for x in null)/256
   effectrows.append({'model':model,'contrast':contrast,'effect_pp':100*t,'p_exploratory':pval,'positive':sum(x>1e-12 for x in v),'negative':sum(x< -1e-12 for x in v),'tied':sum(abs(x)<=1e-12 for x in v)})
 for row in effectrows:
  match=next(r for r in summary['effects'] if r['model']==row['model'] and r['contrast']==row['contrast'])
  assert abs(match['effect_pp']-row['effect_pp'])<1e-6
  assert match['p_exploratory']==row['p_exploratory']
  assert all(match[k]==row[k] for k in ('positive','negative','tied'))
 for model in sorted(meta):
  m=[r for r in cp if r['model']==model]
  cell=next(c for c in summary['cells'] if c['model']==model)
  assert cell['valid']==sum(r['valid'] for r in m) and cell['invalid']==sum(not r['valid'] for r in m)
 primary=sorted([r for r in effectrows if r['contrast']=='FP4_minus_NF4'],key=lambda r:r['p_exploratory'])
 holm=0
 for i,r in enumerate(primary):
  holm=max(holm,min(1,(2-i)*r['p_exploratory']))
  original=next(x for x in summary['effects'] if x['model']==r['model'] and x['contrast']==r['contrast'])
  assert abs(original['holm2_primary_p']-holm)<1e-12
  r['holm2_primary_p']=holm
 with (OUT/'independent_effects.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['model','contrast','effect_pp','p_exploratory','positive','negative','tied','holm2_primary_p'],extrasaction='ignore');w.writeheader();w.writerows(effectrows)
 with (OUT/'independent_publisher_effects.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(pubrows[0]));w.writeheader();w.writerows(pubrows)
 report={'status':'PASS_DECISION_LEVEL_AUDIT','zip_entry_count':len(files),'zip_testzip':'PASS','fp4_checkpoint_count':len(cp),'checkpoint_raw_hashes':'PASS','checkpoint_record_hashes':'PASS','checkpoint_identity':'PASS','checkpoint_schema':'PASS','export_matches_checkpoint':'PASS','baseline_decision_rows':len(baseline),'complete_grid':len(grid),'windows':len(source_by_window),'publisher_rows':len(pubrows),'effect_reproduction':'6/6 PASS','holm2_reproduction':'2/2 PASS','cells':summary['cells'],'effects':effectrows,'limitations':['Full input and E3 gate are not present; original source-text and holdout provenance not independently reverified.','Archived E3 baseline decisions are included but original E3 checkpoint bodies are absent.','Cannot independently rerun CUDA inference, model revision bytes, or four-bit weight quantization from decision records.','Invalid outputs are treated as empty selections under historical Arm A rule; alternate invalid-output sensitivity needs separate evaluation.']}
 (OUT/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
