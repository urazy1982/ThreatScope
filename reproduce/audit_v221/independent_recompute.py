#!/usr/bin/env python3
"""Independent v2.2.1 checkpoint-to-results auditor; no imports from study code."""
from pathlib import Path
from collections import defaultdict,Counter
import hashlib,json,math,itertools,zipfile,statistics,csv,sys
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'outputs_v221'; BASE=ROOT/'baseline_v216.zip'

def enc(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def sha(v): return hashlib.sha256(v).hexdigest()
def read(p): return json.loads(p.read_text())
def sign_p(x):
    xs=list(x); obs=abs(sum(xs)); return sum(abs(sum(a*s for a,s in zip(xs,signs)))>=obs-1e-12 for signs in itertools.product((-1,1),repeat=len(xs)))/2**len(xs)
def holm(p):
    out={};floor=0
    for idx,(k,v) in enumerate(sorted(p.items(),key=lambda kv:kv[1])):
        floor=max(floor,min(1,v*(len(p)-idx)));out[k]=floor
    return out

def interaction(anchors):
    if set(anchors)!=set(range(8)): raise AssertionError('Incomplete anchors')
    total=0
    for target in range(8):
        a=float(target in anchors[target]); others=sum(float(target in anchors[e]) for e in range(8) if e!=target)/7
        total+= (a-others)/8
    return total

def mass_interaction(anchors):
    total=0.
    for target in range(8):
        a=anchors[target][target]; b=sum(anchors[e][target] for e in range(8) if e!=target)/7
        total+=(a-b)/8
    return total

def core():
    manifest=read(ROOT/'RESULT_EXPORT_SHA256.json'); actual=set()
    for rel,digest in manifest.items():
        p=ROOT/rel
        if not p.is_file() or sha(p.read_bytes())!=digest:raise AssertionError('Export SHA mismatch '+rel)
        actual.add(rel)
    extras={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()}-actual
    extras={s for s in extras if s not in ('RESULT_EXPORT_SHA256.json','baseline_v216.zip','independent_recompute.py','compare_arms.py') and not s.startswith('code_') and not s.startswith('independent_')}
    assert not extras, f'Unexpected export files: {list(extras)[:3]}'
    frozen=read(DATA/'authorization.json')['freeze_identity']
    assert frozen['dataset_sha256']=='461682f329a5cca95715d6d7a12356dddb3f38f3adf0e221a2443bdecfdd354e'
    assert frozen['input_sha256']=='e22310e37efe29c2f29f8ec51b931d765a371cc9f7628b52337fa86ce338500b'
    models=list(frozen['model_revisions'])
    allrecs={}; unique_windows={}; counts=Counter(); invalid=Counter(); trunc=Counter(); tie=Counter(); own=Counter(); cardinality=defaultdict(list); copies=Counter(); noncanonical=Counter()
    for p in sorted((DATA/'runs').rglob('example_*/*.json')):
        rec=read(p)
        if rec['record_sha256']!=sha(enc({k:v for k,v in rec.items() if k!='record_sha256'})):raise AssertionError('Checkpoint tampered '+str(p))
        arm=rec['arm'];model=rec['model'];prec=rec['precision'];k=rec['anchor'];win=rec['window_id']
        assert arm in ('B','C','replay') and model in models and prec in ('bf16','nf4') and 0<=k<8
        assert p.name==win+'.json' and p.parent.name=='example_'+str(k)
        assert p.parts[-6:]==('runs',arm,model.split('/')[-1].lower().replace('.','-'),prec,'example_'+str(k),win+'.json')
        assert rec['revision']==frozen['model_revisions'][model]
        assert isinstance(rec['indices'],list) and all(type(x)==int and 0<=x<=7 for x in rec['indices'])
        assert rec['indices']==sorted(set(rec['indices']))
        key=(arm,model,prec,win,k)
        assert key not in allrecs
        allrecs[key]=rec; counts[(arm,model,prec)]+=1
        pair=(win,rec['report_id'],rec['source'],rec['input_sha256'])
        if win in unique_windows:
            assert unique_windows[win]==pair
        unique_windows[win]=pair
        own[(arm,model,prec)]+=int(k in rec['indices'])
        copies[(arm,model,prec)]+=int(rec['indices']==[k])
        cardinality[(arm,model,prec)].append(len(rec['indices']))
        if arm=='C':
            assert rec['valid'] and len(rec['indices'])==1
            scores=rec['scores'];masses=rec['probability_mass']
            assert len(scores)==len(masses)==8 and all(math.isfinite(x) for x in scores+masses)
            top=max(scores);winner=next(j for j,x in enumerate(scores) if x==top)
            assert rec['indices']==[winner] and rec['exact_ties']==sum(x==top for x in scores)
            ex=[math.exp(s-top) for s in scores]; total=sum(ex)
            assert all(abs(masses[j]-ex[j]/total)<1e-8 for j in range(8))
            assert len(set(rec['candidate_token_lengths']))==1
            tie[(model,prec)]+=int(rec['exact_ties']>1)
        else:
            assert rec['raw_sha256']==sha(enc(rec['raw']))
            # raw digest follows canonical JSON string hashing; validate contents below
            try:
                decoded=json.loads(rec['raw'].strip()); idx=decoded['relevant']
                isvalid=isinstance(decoded,dict) and set(decoded)=={'relevant'} and type(idx)==list and len(idx)<=8 and all(type(x)==int and x in range(8) for x in idx) and len(idx)==len(set(idx))
                output=sorted(idx) if isvalid else []
            except (ValueError,TypeError,KeyError,AttributeError):
                isvalid=False;output=[]
            assert isvalid==rec['valid'] and output==rec['indices']
            invalid[(arm,model,prec)]+=int(not isvalid)
            trunc[(arm,model,prec)]+=int(bool(rec.get('cap_reached')))
            if arm=='B':
                assert isvalid and rec['raw']==json.dumps({'relevant':sorted(idx)},separators=(',',':'))
    assert len(allrecs)==14256 and len(unique_windows)==144
    assert len({pair[1] for pair in unique_windows.values()})==72
    src_reports=defaultdict(set); report_windows=Counter()
    for win,report,src,hashid in unique_windows.values():
        src_reports[src].add(report);report_windows[report]+=1
    assert len(src_reports)==9 and all(len(v)==8 for v in src_reports.values())
    assert all(n==2 for n in report_windows.values())
    for arm in ('B','C','replay'):
        for m in models:
            for p in ('bf16','nf4'):
                assert counts[(arm,m,p)]==(72 if arm=='replay' else 1152)
                assert {k[3] for k in allrecs if k[:3]==(arm,m,p)} == (set(unique_windows) if arm!='replay' else {k[3] for k in allrecs if k[:3]==('replay',models[0],'bf16')})
    # Direct record-to-record baseline replay verification from immutable v2.1.6 ZIP
    byte=0;decision=0;validity=0
    with zipfile.ZipFile(BASE) as z:
        names=set(z.namelist())
        for (arm,m,p,w,k),r in allrecs.items():
            if arm!='replay':continue
            fn='outputs/runs/'+m.split('/')[-1].lower().replace('.','-')+'/'+p+'/example_'+str(k)+'/'+w+'.json'
            assert fn in names
            old=json.loads(z.read(fn))
            assert old['record_sha256']==r['baseline_record_sha256']
            assert old['raw']==r['raw'] and r['byte_identical']
            assert old['indices']==r['indices'] and r['decision_identical']
            assert old['valid']==r['valid'] and r['validity_identical']
            byte+=old['raw']==r['raw'];decision+=old['indices']==r['indices'];validity+=old['valid']==r['valid']
    # Independent publisher-equal, report-equal exact analysis
    results=[]; perpub=[]; window_stats=[]; byarm_p=defaultdict(dict)
    for arm in ('B','C'):
        for m in models:
            publishers=defaultdict(lambda:defaultdict(list))
            publishers_mass=defaultdict(lambda:defaultdict(list))
            for w,(_,report,src,inp) in unique_windows.items():
                preds={p:{k:set(allrecs[(arm,m,p,w,k)]['indices']) for k in range(8)} for p in ('bf16','nf4')}
                d={p:interaction(preds[p]) for p in preds}
                effect=d['nf4']-d['bf16'];publishers[src][report].append(effect)
                r={'arm':arm,'model':m,'publisher':src,'report':report,'window':w,'bf16_D':d['bf16'],'nf4_D':d['nf4'],'difference':effect}
                if arm=='C':
                    masses={p:{k:allrecs[(arm,m,p,w,k)]['probability_mass'] for k in range(8)} for p in ('bf16','nf4')}
                    m_d={p:mass_interaction(masses[p]) for p in masses}
                    r.update({'bf16_mass_D':m_d['bf16'],'nf4_mass_D':m_d['nf4'],'mass_difference':m_d['nf4']-m_d['bf16']})
                    publishers_mass[src][report].append(r['mass_difference'])
                window_stats.append(r)
            srcvals={src:sum(sum(vals)/len(vals) for vals in reports.values())/len(reports) for src,reports in publishers.items()}
            d=sum(srcvals.values())/len(srcvals);p=sign_p(srcvals.values());byarm_p[arm][m]=p
            for src,x in srcvals.items():perpub.append({'arm':arm,'model':m,'publisher':src,'delta':x})
            row={'arm':arm,'model':m,'effect':d,'p_exact':p,'positive_publishers':sum(v>0 for v in srcvals.values()),'negative_publishers':sum(v<0 for v in srcvals.values()),'publisher_effects':srcvals,'bf16_mean_cardinality':statistics.mean(cardinality[(arm,m,'bf16')]),'nf4_mean_cardinality':statistics.mean(cardinality[(arm,m,'nf4')]),'bf16_own_example_count':own[(arm,m,'bf16')],'nf4_own_example_count':own[(arm,m,'nf4')],'bf16_exact_copy_count':copies[(arm,m,'bf16')],'nf4_exact_copy_count':copies[(arm,m,'nf4')],'bf16_invalid':invalid[(arm,m,'bf16')],'nf4_invalid':invalid[(arm,m,'nf4')],'bf16_cap_reached':trunc[(arm,m,'bf16')],'nf4_cap_reached':trunc[(arm,m,'nf4')]}
            if arm=='C':
                srcvals_mass={src:sum(sum(vals)/len(vals) for vals in reports.values())/len(reports) for src,reports in publishers_mass.items()}
                row.update({'mass_effect':sum(srcvals_mass.values())/len(srcvals_mass),'mass_p_exact':sign_p(srcvals_mass.values()),'bf16_ties':tie[(m,'bf16')],'nf4_ties':tie[(m,'nf4')]})
            results.append(row)
    family_ps={(r['arm'],r['model']):r['p_exact'] for r in results}
    holm6=holm(family_ps)
    for arm in byarm_p:
        h=holm(byarm_p[arm]);
        for row in results:
            if row['arm']==arm:
                row['p_holm_3']=h[row['model']];row['p_holm_6']=holm6[(arm,row['model'])]
    archived=read(DATA/'audit_summary.json')
    assert archived['status']=='V221_FULL_MATRIX_PASS' and archived['records_verified']==14256
    for row in results:
        a=next(x for x in archived['mechanism_results'] if x['arm']==row['arm'] and x['model']==row['model'])
        assert math.isclose(row['effect'],a['delta'],abs_tol=1e-12) and row['p_exact']==a['p_exact'] and row['p_holm_3']==a['p_holm_within_arm']
        for src,delta in row['publisher_effects'].items():assert math.isclose(delta,a['publisher_effects'][src],abs_tol=1e-12)
    out={'status':'INDEPENDENT_CHECKPOINT_TO_STATISTICS_PASS','export_files_verified':len(manifest),'checkpoint_records_verified':len(allrecs),'replay_byte_identical':byte,'replay_decision_identical':decision,'replay_validity_identical':validity,'unique_windows':len(unique_windows),'reports':len(report_windows),'publishers':len(src_reports),'source_report_counts':{s:len(v) for s,v in src_reports.items()},'runtime_lock':read(DATA/'runtime_lock.json'),'results':results,'caveats':['Output hashing establishes self-consistency, not independent GPU inference reproduction.','Arm C changes the task and uses forced-choice likelihood scoring; it is not a pure cardinality intervention.','Arm B constrained generation may change decisions beyond format validity.','Results are not externally preregistered; human gold labels absent.']}
    (ROOT/'independent_v221_results.json').write_text(json.dumps(out,indent=2)+'\n')
    for fn,rows in [('independent_window_effects.csv',window_stats),('independent_publisher_effects.csv',perpub)]:
        with (ROOT/fn).open('w',newline='') as f:
            c=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for row in rows for k in row)));c.writeheader();c.writerows(rows)
    print('PASS export files',len(manifest),'records',len(allrecs),'replay',byte,decision,validity,'sources',len(src_reports))
    for row in results:
        print(row['arm'],row['model'].split('/')[-1],f"effect={row['effect']*100:+.4f}pp", 'p=',row['p_exact'],'Holm3=',row['p_holm_3'],'Holm6=',row['p_holm_6'],'card=',round(row['bf16_mean_cardinality'],3),round(row['nf4_mean_cardinality'],3), 'copy=',row['bf16_exact_copy_count'],row['nf4_exact_copy_count'], 'ties=',row.get('bf16_ties'),row.get('nf4_ties'), 'mass=',row.get('mass_effect'), 'mass_p=',row.get('mass_p_exact'))
    return out

if __name__=='__main__':core()
