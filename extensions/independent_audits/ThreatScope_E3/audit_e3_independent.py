import zipfile,json,csv,io,hashlib,collections,itertools,math,statistics,os
P='/mnt/data/ThreatScope_E3_v0_4_Complete_GPU_Results.zip'; Z=zipfile.ZipFile(P); root='ThreatScope_E3_GPU_v0_4/'
get=lambda name:Z.read(root+name)
js=lambda name:json.loads(get(name))
rows=list(csv.DictReader(io.StringIO(get('results/reports/E3_decisions_textfree.csv').decode())))
win=list(csv.DictReader(io.StringIO(get('results/reports/E3_window_effects.csv').decode())))
pub=list(csv.DictReader(io.StringIO(get('results/reports/E3_publisher_effects.csv').decode())))
summ=js('results/reports/E3_summary.json'); audit=js('results/reports/E3_audit.json'); manifest=js('SHA256_MANIFEST.json')
file_hashes={n:hashlib.sha256(get(n)).hexdigest()==h for n,h in manifest.items()}
by=collections.defaultdict(dict); problems=[]; counts=collections.Counter(); models=set(); sources=set(); meta_hash=[]; samples=[]
for n in Z.namelist():
 if '/example_' not in n or not n.endswith('.json'): continue
 v=json.loads(Z.read(n)); rel=n[len(root):]; seg=rel.split('/'); model_dir,prec,ex=seg[2],seg[3],seg[4]; k=int(ex.split('_')[1]); key=(v['model'],prec,v['window_id']);
 if v['anchor']!=k or v['precision']!=prec:problems.append(('identity',n))
 if k in by[key]:problems.append(('duplicate',n))
 by[key][k]=v
 counts[(v['model'],prec)]+=1;models.add(v['model']);
 if hashlib.sha256(json.dumps(v['raw'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=v['raw_sha256']:problems.append(('rawsha',n))
 nohash={x:y for x,y in v.items() if x!='record_sha256'}
 if hashlib.sha256(json.dumps(nohash,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=v['record_sha256']:problems.append(('recsha',n))
 # independent parse semantics, strict exact schema
 try:
  parsed=json.loads(v['raw']);valid=isinstance(parsed,dict) and set(parsed)=={'relevant'} and isinstance(parsed['relevant'],list) and all(type(x)==int and 0<=x<=7 for x in parsed['relevant']) and len(set(parsed['relevant']))==len(parsed['relevant'])
 except Exception:valid=False
 if bool(v['valid'])!=valid:problems.append(('parser',n,v['raw'][:100]));
 if v['valid'] and v['indices']!=sorted(parsed['relevant']):problems.append(('indices',n))
seen_rows=set(); validcounts=collections.Counter(); decwrong=[]
for r in rows:
 key=(r['model'],r['precision'],r['window_id']);k=int(r['anchor']); seen_rows.add((key,k))
 a=by.get(key,{}).get(k)
 if a is None:decwrong.append(('missing',key,k));continue
 if str(a['valid'])!=r['valid'] or a['indices']!=json.loads(r['indices']) or a['prompt_sha256']!=r['prompt_sha256'] or a['record_sha256']!=r['record_sha256']:decwrong.append(('mismatch',key,k))
 validcounts[(r['model'],r['precision'])]+=r['valid']=='True'
W={};
for key,recs in by.items():
 if set(recs)!=set(range(8)):problems.append(('missinganchor',key));continue
 ds=[]
 for k in range(8):
  for j in range(8):ds.append((k,j,int(bool(recs[k]['valid']) and j in recs[k]['indices'])))
 D=sum(v for k,j,v in ds if k==j)/8-sum(v for k,j,v in ds if k!=j)/56
 W[key]=D
wwrong=[]
for r in win:
 key=(r['model'],r['precision'],r['window_id'])
 if key not in W or abs(W[key]-float(r['D']))>1e-12:wwrong.append(key)
S=collections.defaultdict(dict);pubwrong=[];pvs=collections.defaultdict(list)
for r in win:pvs[(r['model'],r['source'],r['precision'])].append(float(r['D']))
for r in pub:
 m,s=r['model'],r['source'];a=statistics.mean(pvs[(m,s,'bf16')]);b=statistics.mean(pvs[(m,s,'nf4')]);d=b-a
 if any(abs(x-y)>1e-12 for x,y in zip((a,b,d),(float(r['D_bf16']),float(r['D_nf4']),float(r['delta'])))):pubwrong.append((m,s));
 S[m][s]=d
out=[]
for m, groups in S.items():
 vals=list(groups.values()); mean=statistics.mean(vals); allp=[abs(statistics.mean(v*s for v,s in zip(vals,signs))) for signs in itertools.product([-1,1],repeat=len(vals))];p=sum(t>=abs(mean)-1e-12 for t in allp)/len(allp)
 sign=collections.Counter('pos' if v>1e-12 else 'neg' if v<-1e-12 else 'tie' for v in vals)
 loo=[statistics.mean([v for s,v in groups.items() if s!=k])*100 for k in groups]
 out.append({'model':m,'delta_pp':mean*100,'signflip_p':p,'positive':sign['pos'],'negative':sign['neg'],'zero':sign['tie'],'leave_one_publisher_out_min_pp':min(loo),'leave_one_publisher_out_max_pp':max(loo)})
for r in out:
 q=next(x for x in summ['rows'] if x['model']==r['model']);r['reported_delta_match']=abs(r['delta_pp']-q['nf4_minus_bf16_pp'])<1e-5;r['reported_p_match']=r['signflip_p']==q['exact_signflip_p_exploratory']
ps=sorted((x['signflip_p'],i) for i,x in enumerate(out)); acc=0
for rank,(p,i) in enumerate(ps):acc=max(acc,min(1,(len(ps)-rank)*p));out[i]['holm3_p']=acc
report={'zip_testzip':Z.testzip(),'member_count':len(Z.namelist()),'tracked_code_hashes':len(manifest),'tracked_hashes_all_pass':all(file_hashes.values()),'checkpoint_count':sum(counts.values()),'per_cell_counts':{f'{m} / {p}':n for (m,p),n in counts.items()},'checkpoint_structural_issues':problems[:20],'checkpoint_issue_count':len(problems),'decision_rows':len(rows),'decision_comparison_errors':len(decwrong),'window_rows':len(win),'window_D_comparison_errors':len(wwrong),'publisher_rows':len(pub),'publisher_comparison_errors':len(pubwrong),'summary':out,'audit_input_hash':audit['input_sha256'],'expected_input_hash':'84c02a30c6f077d1c2d0e645be480616e66d93dd61ca5d660acb77bed37216b3','source_text_present':any('sentence_text' in json.dumps(v) for d in by.values() for v in d.values()),'freeze_inputs_present':any('inputs_E3_private' in n for n in Z.namelist()),'gate_report_present':any(n.endswith('/GATE.json') for n in Z.namelist()),'status':'PASS' if not problems and not decwrong and not wwrong and not pubwrong and all(file_hashes.values()) else 'FAIL'}
with open('/mnt/data/E3_independent_verification.json','w') as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
