"""Read-only audit of authentic uploaded *derived data*, not raw LLM checkpoints."""
from __future__ import annotations
import argparse,collections,csv,hashlib,io,itertools,json,statistics,zipfile
from pathlib import Path

def load_csv(z,name):
    with z.open('outputs/analysis/'+name+'.csv') as src:
        return list(csv.DictReader(io.TextIOWrapper(src,encoding='utf8')))

def exact_signflip(vals):
    x=list(map(float,vals)); obs=abs(sum(x)); signs=itertools.product((-1,1),repeat=len(x))
    return sum(abs(sum(v*s for v,s in zip(x,sgn))) >= obs-1e-12 for sgn in signs)/(2**len(x))

def run(audit_file,analysis_zip):
    audit=json.loads(Path(audit_file).read_text())
    assert audit['files_read']==298 and audit['parse_errors']==[]
    assert audit['unique_exact_texts']==148 and audit['unique_normalized_texts']==148
    assert audit['source_label_coverage']==0
    assert audit['by_partition']=={'annotation':149,'demo':139,'test':10}
    assert len(audit['exact_duplicate_groups'])==148
    hist=collections.Counter(x['count'] for x in audit['exact_duplicate_groups'])
    assert hist=={2:147,4:1},hist
    assert sum(x['count'] for x in audit['exact_duplicate_groups'])==298
    sets={k:set(v) for k,v in audit['partition_sets'].items()}
    assert sets['annotation']==sets['demo']|sets['test']
    assert not sets['demo']&sets['test']
    assert len(sets['annotation'])==148 and len(sets['demo'])==138 and len(sets['test'])==10
    with zipfile.ZipFile(analysis_zip) as z:
        names=('arm_metrics','window_diagnostics','report_anchor_counts','source_interactions','prompt_interactions','direct_prompt_flips')
        summary=json.loads(z.read('outputs/analysis/SUMMARY.json'))
        for name in names:
            body=z.read('outputs/analysis/'+name+'.csv')
            assert hashlib.sha256(body).hexdigest()==summary['files_sha256'][name+'.csv'],name
        arms=load_csv(z,'arm_metrics')
        windows=load_csv(z,'window_diagnostics')
        sources=load_csv(z,'source_interactions')
        prompt=load_csv(z,'prompt_interactions')
        flips=load_csv(z,'direct_prompt_flips')
    assert len(arms)==12 and len(windows)==3408 and len(sources)==15 and len(prompt)==3 and len(flips)==1704
    assert len({w['window_id'] for w in windows})==284
    assert len({w['doc_id'] for w in windows})==40
    assert len({w['source'] for w in windows})==5
    assert sum(int(w['valid'])==0 for w in windows)==20
    assert sum(w['origin']=='legacy_v141' for w in windows)==289
    assert sum(int(x['exact_0_to_4_switch']) for x in flips)==1
    assert all(int(x['example_token_parity'])==1 for x in windows)
    for arm in arms:
        rr=[w for w in windows if w['model']==arm['model'] and w['precision']==arm['precision'] and w['condition']==arm['condition']]
        assert len(rr)==284
        for metric in ('tp','fp','fn','tn'):
            assert sum(int(w[metric]) for w in rr)==int(arm[metric]),(metric,arm['model'])
        assert sum(int(w['valid']) for w in rr)==int(arm['valid'])
        assert sum(int(w['generation_cap_reached']) for w in rr)==0
    primary=[]
    for r in prompt:
        model=r['model']; source_effects=[float(x['interaction']) for x in sources if x['model']==model]
        assert len(source_effects)==5 and all(x>0 for x in source_effects)
        p=exact_signflip(source_effects)
        assert abs(p-float(r['source_exact_p']))<1e-12
        assert abs(p-0.0625)<1e-12
        assert abs(float(r['holm_source_p'])-0.1875)<1e-12
        primary.append({'model':model,'delta':float(r['nf4_minus_bf16_prompt_content_interaction']),
                        'source_exact_p':p,'holm_source_p':float(r['holm_source_p'])})
    return {'ctinexus':{'files':298,'unique_reports':148,'exact_duplicate_histogram':dict(hist),'source_label_coverage':0,
                       'annotation_unique':148,'demo_unique':138,'test_unique':10,'publisher_test_supported':False},
            'v151':{'analytical_csv_hashes_verified':6,'window_records':len(windows),'arm_records':len(arms),
                    'reports':40,'sources':5,'invalid_outputs':20,'legacy_imported':289,
                    'exact_singleton_example_0_to_4_switches':1,'source_level_results':primary,
                    'limit':'Derived-data reanalysis, not original model inference or article-text authenticity verification'}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--ctinexus-audit',required=True);p.add_argument('--v151-zip',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();res=run(a.ctinexus_audit,a.v151_zip)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(res,indent=2)+'\n')
    print('REAL_DERIVED_EVIDENCE_AUDIT_PASS',len(res['v151']['source_level_results']),'models',res['ctinexus']['unique_reports'],'unique CTINexus texts')
if __name__=='__main__':main()
