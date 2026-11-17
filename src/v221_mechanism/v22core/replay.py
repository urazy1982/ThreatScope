"""Independently verify and reanalyze every v2.1.6 GPU checkpoint on CPU.

No pretrained model, tokenizer, GPU, network, or human gold labels required.
"""
from __future__ import annotations
import collections,csv,hashlib,itertools,json,math,random,zipfile
from pathlib import Path
from .core import SYS,prompt,parse,digest,original_effect,mass_effect,exact_p,holm


def open_archive(path):
    z=zipfile.ZipFile(path)
    if z.testzip() is not None:raise RuntimeError('CORRUPT_ARCHIVE')
    return z

def read_json(z,path):return json.loads(z.read(path))
def cell_id(model,prec):return model.split('/')[-1].lower().replace('.','-')+'/'+prec

def validate_archive(path):
    with open_archive(path) as z:
        cfg=read_json(z,'config/study.json');m=read_json(z,'outputs/prepared/manifest.json')
        if cfg['protocol']!=m['protocol']:raise RuntimeError('PROTOCOL_MISMATCH')
        if hashlib.sha256(z.read('config/study.json')).hexdigest()!=m['config_sha256']:
            raise RuntimeError('CONFIG_HASH_MISMATCH')
        raw_inputs=z.read('outputs/prepared/inputs.jsonl')
        if hashlib.sha256(raw_inputs).hexdigest()!=m['input_sha256']:
            raise RuntimeError('PREPARED_INPUT_HASH_MISMATCH')
        windows=[json.loads(x) for x in raw_inputs.decode().splitlines() if x.strip()]
        if len(windows)!=144 or m['windows']!=len(windows):raise RuntimeError('WINDOW_COUNT_MISMATCH')
        ids={w['window_id']:w for w in windows}
        if len(ids)!=144:raise RuntimeError('DUPLICATE_WINDOWS')
        reports=collections.defaultdict(set)
        for w in windows:
            if len(w['sentences'])!=8:raise RuntimeError('NOT_EIGHT_SENTENCES')
            h=w['input_sha256'];payload={k:v for k,v in w.items() if k!='input_sha256'}
            if digest(payload)!=h:raise RuntimeError('WINDOW_HASH_DRIFT')
            reports[w['source']].add(w['report_id'])
        if len(reports)!=9 or any(len(x)!=8 for x in reports.values()):raise RuntimeError('UNBALANCED_PUBLISHERS')
        rows={};counters=collections.Counter()
        for model,revision in cfg['models'].items():
            for precision in cfg['precisions']:
                base='outputs/runs/'+cell_id(model,precision)
                meta=read_json(z,base+'/run_metadata.json')
                expected={'protocol':cfg['protocol'],'model':model,'revision':revision,'precision':precision,
                    'prepared_input_sha256':m['input_sha256'],'config_sha256':m['config_sha256'],
                    'prompt_sha256':digest(SYS),'decoding':{'do_sample':False,'num_beams':1,
                    'max_new_tokens':cfg['max_new_tokens']},'torch_dtype':'bfloat16',
                    'attention_implementation':'sdpa',
                    'python_package_lock':'torch-transformers-bitsandbytes-versions-in-environment_metadata'}
                if meta!=expected:raise RuntimeError('CELL_METADATA_DRIFT '+base)
                meta_sha=digest(meta)
                env=read_json(z,base+'/environment.json')
                if env['revision']!=revision:raise RuntimeError('ENVIRONMENT_MODEL_DRIFT')
                counters['environment_cells_verified']+=1
                for w in windows:
                    for k in range(8):
                        file=base+f'/example_{k}/'+w['window_id']+'.json'
                        rec=read_json(z,file)
                        ex={'window_id':w['window_id'],'input_sha256':w['input_sha256'],
                            'anchor':k,'model':model,'precision':precision,'revision':revision,
                            'identity_sha256':meta_sha,'prompt_sha256':digest([SYS,prompt(w,k),model])}
                        if any(rec.get(key)!=value for key,value in ex.items()):
                            raise RuntimeError('RECORD_IDENTITY_DRIFT '+file)
                        if rec['raw_sha256']!=digest(rec['raw']):raise RuntimeError('RAW_HASH_DRIFT '+file)
                        if rec['record_sha256']!=digest({a:b for a,b in rec.items() if a!='record_sha256'}):
                            raise RuntimeError('RECORD_HASH_DRIFT '+file)
                        rerender=parse(rec['raw'])
                        if any(rec[key]!=rerender[key] for key in ['valid','indices','error']):
                            raise RuntimeError('PARSER_REPLAY_MISMATCH '+file)
                        if rec['generation_cap_reached']!=(rec['generated_tokens']>=cfg['max_new_tokens']):
                            raise RuntimeError('TOKEN_CAP_FLAG_MISMATCH '+file)
                        rows[(model,precision,w['window_id'],k)]=rec
                        counters['checkpoints_verified']+=1
                        counters['invalid_outputs']+=int(not rec['valid'])
        actual_paths={x for x in z.namelist() if '/example_' in x and x.endswith('.json') and x.startswith('outputs/runs/')}
        if len(actual_paths)!=counters['checkpoints_verified']:raise RuntimeError('EXTRA_RECORDS')
        if counters['checkpoints_verified']!=6912:raise RuntimeError('INCOMPLETE_MATRIX')
        if cfg['models'].keys()!=set(k[0] for k in rows):raise RuntimeError('MODEL_MATRIX_MISMATCH')
        return cfg,m,windows,rows,dict(counters)

def ci_bootstrap_by_source(source_reports,draws=10000,seed=20261113):
    rng=random.Random(seed);sources=sorted(source_reports)
    v=[]
    for _ in range(draws):
        samples=[]
        for source in [rng.choice(sources) for _ in sources]:
            reports=list(source_reports[source].values())
            samples.append(sum(rng.choice(reports) for _ in reports)/len(reports))
        v.append(sum(samples)/len(samples))
    v.sort()
    return [v[int(.025*(draws-1))],v[int(.975*(draws-1))]]

def compute(cfg,m,windows,rows):
    models=list(cfg['models']);per_window=[];publisher_table=[];summary=[];index_rows=[];src_by_model={}
    for model in models:
        src_reports=collections.defaultdict(lambda:collections.defaultdict(list))
        src_mass=collections.defaultdict(lambda:collections.defaultdict(list))
        copy=collections.Counter();invalid=collections.Counter();total=collections.Counter();diag=collections.Counter();valid_pair=[]
        for w in windows:
            per={}
            for prec in ('bf16','nf4'):
                rec=[rows[(model,prec,w['window_id'],k)] for k in range(8)]
                selected={k:set(rec[k]['indices']) if rec[k]['valid'] else set() for k in range(8)}
                effect=original_effect(selected);mass=mass_effect(selected)
                per[prec]=(effect,mass,all(r['valid'] for r in rec))
                total[prec]+=effect['C'];diag[prec]+=effect['T']
                copy[prec]+=sum(rec[k]['valid'] and rec[k]['indices']==[k] for k in range(8))
                invalid[prec]+=sum(not r['valid'] for r in rec)
                for k,r in enumerate(rec):
                    index_rows.append({'model':model,'precision':prec,'source':w['source'],'anchor':k,
                    'valid':int(r['valid']),'cardinality':len(selected[k]),
                    'self_selected':int(k in selected[k]),'singleton_copy':int(r['valid'] and r['indices']==[k])})
            diff=per['nf4'][0]['effect']-per['bf16'][0]['effect']
            dm=per['nf4'][1]['effect']-per['bf16'][1]['effect']
            dt=(per['nf4'][0]['T']-per['bf16'][0]['T'])/7
            dc=-(per['nf4'][0]['C']-per['bf16'][0]['C'])/56
            if not math.isclose(diff,dt+dc,rel_tol=0,abs_tol=1e-12):raise AssertionError('INTERACTION_DECOMP')
            per_window.append({'model':model,'source':w['source'],'report_id':w['report_id'],
               'window_id':w['window_id'],'raw_interaction':diff,'mass_interaction':dm,
               'diagonal_contribution':dt,'cardinality_contribution':dc,
               'complete_valid':int(per['bf16'][2] and per['nf4'][2])})
            src_reports[w['source']][w['report_id']].append(diff)
            src_mass[w['source']][w['report_id']].append(dm)
            valid_pair.append((w['source'],w['report_id'],diff,per['bf16'][2] and per['nf4'][2]))
        original_src={};mass_src={}
        for s in cfg['source_names']:
            if s not in src_reports:raise RuntimeError('SOURCE_MISSING')
            original_src[s]=sum(sum(v)/len(v) for v in src_reports[s].values())/len(src_reports[s])
            mass_src[s]=sum(sum(v)/len(v) for v in src_mass[s].values())/len(src_mass[s])
            publisher_table.append({'model':model,'publisher':s,'raw_interaction':original_src[s],
                'mass_interaction':mass_src[s],'reports':len(src_reports[s])})
        n=len(windows)
        mean=sum(original_src.values())/len(original_src)
        norm=sum(mass_src.values())/len(mass_src)
        mean_d=(diag['nf4']-diag['bf16'])/(7*n)
        mean_c=-(total['nf4']-total['bf16'])/(56*n)
        if not math.isclose(mean,mean_d+mean_c,rel_tol=0,abs_tol=1e-12):raise AssertionError('SOURCE_WEIGHT_DRIFT')
        all_valid=[x for x in valid_pair if x[3]]
        source_valid=collections.defaultdict(lambda:collections.defaultdict(list))
        for s,r,d,_ in all_valid:source_valid[s][r].append(d)
        valid_stat=None; valid_p=None
        if len(source_valid)==len(cfg['source_names']):
            valid_means=[sum(sum(v)/len(v) for v in source_valid[s].values())/len(source_valid[s])
                         for s in sorted(source_valid)]
            valid_stat=sum(valid_means)/len(valid_means);valid_p=exact_p(valid_means)
        summary.append({'model':model,'raw_delta':mean,'raw_p':exact_p(original_src.values()),
            'raw_ci_95':ci_bootstrap_by_source({s:{r:sum(v)/len(v) for r,v in x.items()} for s,x in src_reports.items()}),
            'mass_normalized_delta_exploratory':norm,'mass_p_exploratory':exact_p(mass_src.values()),
            'mass_ci_95':ci_bootstrap_by_source({s:{r:sum(v)/len(v) for r,v in x.items()} for s,x in src_mass.items()}),
            'raw_diagonal_contribution':mean_d,'raw_cardinality_contribution':mean_c,
            'bf16_own_example_count':diag['bf16'],'nf4_own_example_count':diag['nf4'],
            'bf16_total_selected':total['bf16'],'nf4_total_selected':total['nf4'],
            'bf16_invalid':invalid['bf16'],'nf4_invalid':invalid['nf4'],
            'bf16_singleton_copy':copy['bf16'],'nf4_singleton_copy':copy['nf4'],
            'valid_pair_windows':len(all_valid),'valid_only_delta':valid_stat,
            'valid_only_p':valid_p,
            'leave_one_publisher_out_raw_range':[min(sum(v for ss,v in original_src.items() if ss!=s)/8 for s in original_src),
                                                   max(sum(v for ss,v in original_src.items() if ss!=s)/8 for s in original_src)],
            'leave_one_publisher_out_mass_range':[min(sum(v for ss,v in mass_src.items() if ss!=s)/8 for s in mass_src),
                                                   max(sum(v for ss,v in mass_src.items() if ss!=s)/8 for s in mass_src)]})
        src_by_model[model]=original_src
    correction=holm({x['model']:x['raw_p'] for x in summary})
    correction_mass=holm({x['model']:x['mass_p_exploratory'] for x in summary})
    for entry in summary:
        entry['raw_holm']=correction[entry['model']]
        entry['mass_holm_exploratory']=correction_mass[entry['model']]
    pairwise=[]
    for a,b in itertools.combinations(models,2):
        vals=[src_by_model[a][s]-src_by_model[b][s] for s in cfg['source_names']]
        pairwise.append({'model_a':a,'model_b':b,'between_model_delta':sum(vals)/len(vals),
                         'source_signflip_p_exploratory':exact_p(vals)})
    return {'dataset_sha256':m['dataset_sha256'],'input_sha256':m['input_sha256'],
        'models':summary,'source_count':9,'windows':len(windows),'records':len(rows),
        'source_pairwise_differences_exploratory':pairwise,
        'limitations':['All additional effects beyond the v2.1.6 original statistic are posthoc/exploratory.',
            'Uniform-over-selected-set mass is not teacher-forced candidate probability.',
            'No human gold labels; no accuracy or false-positive claims.',
            'No v2.2 Arm B/C LLM inference on the CPU server.']},per_window,publisher_table,index_rows

def write_csv(path,rows):
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run(archive,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    cfg,m,windows,rows,audit=validate_archive(archive)
    outcome,per,source,ix=compute(cfg,m,windows,rows)
    # Compare untouched v2.1.6 headline numbers to the archived analysis independently.
    with open_archive(archive) as z:base=read_json(z,'outputs/analysis/summary.json')
    old={x['model']:x for x in base['models']}
    for new in outcome['models']:
        x=old[new['model']]
        for key,ours in [('source_equal_interaction',new['raw_delta']),('source_signflip_two_sided_p',new['raw_p']),('holm_p',new['raw_holm'])]:
            if not math.isclose(x[key],ours,abs_tol=1e-13,rel_tol=0):raise RuntimeError('ARCHIVED_PRIMARY_DISAGREEMENT '+key)
        if (x['invalid_bf16'],x['invalid_nf4'])!=(new['bf16_invalid'],new['nf4_invalid']):
            raise RuntimeError('INVALID_RECORD_COUNT_DISAGREEMENT')
    write_csv(out/'per_window_derived.csv',per)
    write_csv(out/'publisher_derived.csv',source)
    write_csv(out/'per_index_outputs.csv',ix)
    (out/'real_checkpoint_validation.json').write_text(json.dumps(audit,indent=2)+'\n')
    (out/'cpu_main_results.json').write_text(json.dumps(outcome,indent=2)+'\n')
    return outcome,audit

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();res,audit=run(a.archive,a.out)
    print(json.dumps({'status':'CPU_REAL_RESULTS_REANALYSIS_PASS','audit':audit,'models':res['models']},indent=2))
