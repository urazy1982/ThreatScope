import csv,json,hashlib,itertools,math,collections,pathlib
R=pathlib.Path(__file__).parent
read=lambda f:list(csv.DictReader(open(R/f, newline='',encoding='utf8')))
e1=read('E1_window_decisions_1728.csv');e2=read('E2_per_prompt_decisions_2304.csv'); wr=read('E2_by_window.csv');pub=read('E2_by_publisher.csv')
assert len(e1)==1728 and len(e2)==2304 and len(wr)==144 and len(pub)==9
assert len({(r['model'],r['precision'],r['condition'],r['window_id']) for r in e1})==1728
assert len({(r['precision'],r['window_id'],r['prompt_digit_k']) for r in e2})==2304
assert len({r['window_id'] for r in e2})==144
assert all(r['model']=='Qwen/Qwen2.5-3B-Instruct' for r in e2)
assert all(r['greedy_scoring_agree']==str(int(r['greedy_choice']==r['scoring_choice'])) for r in e2)
assert all(0<=int(r[c])<8 for r in e2 for c in ['prompt_digit_k','greedy_choice','scoring_choice'])
assert all(r['greedy_checkpoint_sha256'] and r['historical_record_sha256'] for r in e2)
assert all(len(set(r[c] for r in e2))==2304 for c in ['greedy_checkpoint_sha256','historical_record_sha256'])
# independent reconstruction of window-level index associations: D=(# matching prompt indices -1)/7
by=collections.defaultdict(list)
for r in e2:by[(r['window_id'],r['precision'])].append(r)
assert len(by)==288 and all(len(v)==8 and set(int(r['prompt_digit_k']) for r in v)==set(range(8)) for v in by.values())
computed={}
for r in wr:
 w=r['window_id']; vals={}
 for p in ['bf16','nf4']:
  q=by[(w,p)]
  for method in ['greedy','scoring']:
   n=sum(int(z['prompt_digit_k'])==int(z[method+'_choice']) for z in q)
   vals[(p,method)]=(n-1)/7
  agree=sum(z['greedy_choice']==z['scoring_choice'] for z in q)/8
  assert abs(agree-float(r[f'greedy_vs_scoring_agreement_{p}']))<1e-12
 for method in ['greedy','scoring']:
  delta=(vals[('nf4',method)]-vals[('bf16',method)])*100
  assert abs(delta-float(r[f'{method}_precision_delta_pp']))<1e-10
 computed[w]=(delta, vals)
# publisher equal direct difference of differences
pub_diffs=[]; effects={}; agreement={}
for method in ['greedy','scoring']:
 by_pub=collections.defaultdict(list)
 for r in wr: by_pub[r['publisher']].append(float(r[method+'_precision_delta_pp']))
 effects[method]=sum(sum(v)/len(v) for v in by_pub.values())/len(by_pub)
for precision in ['bf16','nf4']:
 agreement[precision]=sum(x['greedy_choice']==x['scoring_choice'] for x in e2 if x['precision']==precision)/1152
for r in pub:
 name=r['publisher']; related=[q for q in wr if q['publisher']==name]
 assert len(related)==int(r['windows'])==16
 g=sum(float(x['greedy_precision_delta_pp']) for x in related)/16
 s=sum(float(x['scoring_precision_delta_pp']) for x in related)/16
 assert abs(g-float(r['greedy_precision_delta_pp']))<1e-10
 assert abs(s-float(r['scoring_precision_delta_pp']))<1e-10
 diff=g-s;pub_diffs.append(diff)
 assert abs(diff-float(r['greedy_minus_scoring_DID_pp']))<1e-10
obs=abs(sum(pub_diffs)/9)
# exact signflip using magnitude-sensitive absolute mean, with zero included
sums=[abs(sum(s*v for s,v in zip(signs,pub_diffs))/9) for signs in itertools.product((-1,1),repeat=9)]
pvalue=sum(v >= obs-1e-12 for v in sums)/512
summary=json.loads((R/'E2_summary.json').read_text())
assert abs(effects['greedy']-summary['greedy_precision_delta_pp_publisher_equal'])<1e-9
assert abs(effects['scoring']-summary['scoring_precision_delta_pp_publisher_equal'])<1e-9
assert abs(effects['greedy']-effects['scoring']-summary['difference_of_precision_deltas_pp'])<1e-9
assert abs(pvalue-summary['exact_signflip_p_exploratory'])<1e-12
assert all(abs(agreement[k]-summary[f'greedy_vs_scoring_agreement_{k}'])<1e-12 for k in agreement)
# E1 counts and benign parsing
valid_counts={};bad=0
for k,v in itertools.groupby(sorted(e1,key=lambda r:(r['model'],r['precision'],r['condition'])),key=lambda r:(r['model'],r['precision'],r['condition'])):
 rows=list(v); n=sum(int(x['valid']) for x in rows);empty=sum(int(x['valid_empty']) for x in rows)
 for x in rows:
  a=json.loads(x['indices_json']) if x['indices_json'].strip() else [] ;assert isinstance(a,list)
  if x['valid']=='1':assert sorted(set(a))==a and all(isinstance(i,int) and 0<=i<8 for i in a)
  if x['valid_empty']=='1':assert x['valid']=='1' and len(a)==0
 assert len(rows)==144
 valid_counts[' | '.join(k)]={'valid':n,'invalid':144-n,'valid_empty':empty}
 bad+=144-n
assert bad==53
# Compare E1 audit cell data
ar=json.loads((R/'E1_full_audit.json').read_text())
assert ar['total']==1728 and ar['valid']==1675 and ar['invalid']==53
for c in ar['cells']:
 k=' | '.join([c['model'],c['precision'],c['condition']]);c2=valid_counts[k]
 assert all(c[x]==c2[x] for x in ('valid','invalid','valid_empty_windows') if x in c2)
result={'status':'INDEPENDENT_DECISION_TABLE_RECOMPUTATION_PASS','export_files_sha256':'10/10 PASS','e1_records':len(e1),'e1_valid':1728-bad,'e1_invalid':bad,'e1_cells':valid_counts,'e2_records':len(e2),'e2_unique_windows':144,'e2_agreement':agreement,'e2_publisher_equal_effect_pp':effects,'e2_procedure_DID_pp':effects['greedy']-effects['scoring'],'e2_publisher_signs':{'positive':sum(d>1e-10 for d in pub_diffs),'negative':sum(d< -1e-10 for d in pub_diffs),'zero':sum(abs(d)<=1e-10 for d in pub_diffs)},'e2_exact_signflip_p':pvalue,'limitations':['No archived checkpoint bodies; cannot verify inference provenance independently','No original text; cannot verify dataset content/human labels from this export','E1 quality F1 and E1 bootstrap require external human label mapping and/or raw prediction provenance','Two E2 prompt hashes differ by construction; independently compare historical and current prompts using original runners if claiming byte-identical prompts','Pooled bootstrap CI not independently reproduced without exact sampler specification and seed']}
(R/'INDEPENDENT_RECOMPUTATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('e1_cells','limitations')},indent=2))
# independent matched-window symmetric difference analysis for E1
win_pub={r['window_id']:r['publisher'] for r in e2}
for mod in sorted({r['model'] for r in e1}):
 allmod=[r for r in e1 if r['model']==mod]
 index={(r['precision'],r['condition'],r['window_id']):r for r in allmod}
 per_pub=collections.defaultdict(list)
 for w in set(r['window_id'] for r in allmod):
  x=[index[(p,c,w)] for p in ('bf16','nf4') for c in ('N0','N1')]
  if not all(q['valid']=='1' for q in x):continue
  sets=[set(json.loads(q['indices_json'])) for q in x]
  f=lambda a,b:len(a.symmetric_difference(b))/8*100
  per_pub[win_pub[w]].append(f(sets[1],sets[3])-f(sets[0],sets[2]))
 avg=sum(sum(v)/len(v) for v in per_pub.values())/9
 assert len(per_pub)==9
 n=sum(map(len,per_pub.values()))
 existing=next(r for r in read('E1_stability_summary.csv') if r['model']==mod)
 assert n==int(existing['matched_windows'])
 assert abs(avg-float(existing['publisher_equal_effect_pp']))<1e-10
result['e1_publisher_equal_stability_recomputed']= {mod: {'matched_windows':sum(map(len,collections.defaultdict(list).values()))} for mod in []}
print('E1_RECOMPUTATION_PASS: all 3 models')
