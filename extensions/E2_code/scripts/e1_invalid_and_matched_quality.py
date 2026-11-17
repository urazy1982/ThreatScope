#!/usr/bin/env python3
"""Read-only CPU reanalysis of completed E1; distinguishes output validity from selection quality.

Provides intent-to-treat F1, valid-only (different denominator), and exact four-way
matched subset F1 (same denominator across all four cells per model).
The original 288 adjudicated labels are imperfect and should not be called gold.
"""
import argparse,csv,hashlib,json,math,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vendor.e1_neutral_gpu import verify_frozen_inputs,sha,canonical
MODELS={'Qwen/Qwen2.5-3B-Instruct':'qwen2.5-3b',
        'meta-llama/Llama-3.2-3B-Instruct':'llama-3.2-3b',
        'mistralai/Mistral-7B-Instruct-v0.3':'mistral-7b'}

def f1(rows):
    tp=sum(ref==1 and pred==1 for ref,pred in rows)
    fp=sum(ref==0 and pred==1 for ref,pred in rows)
    fn=sum(ref==1 and pred==0 for ref,pred in rows)
    tn=sum(ref==0 and pred==0 for ref,pred in rows)
    return {'n':len(rows),'TP':tp,'FP':fp,'FN':fn,'TN':tn,'F1':2*tp/(2*tp+fp+fn) if (2*tp+fp+fn)>0 else 0.0}

def write(path,rows):
    if not rows:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as h:
        wr=csv.DictWriter(h,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)

def pair_p(a,b):
    # Exploratory exact paired Bernoulli test; windows are clustered by publisher/report.
    n=a+b
    if not n:return 1.0
    return min(1.0,2*sum(math.comb(n,k) for k in range(min(a,b)+1))/2**n)

def run(inputs,manifest,results,labels,out):
    m,windows,cfg=verify_frozen_inputs(inputs,manifest)
    byid={w['window_id']:w for w in windows}
    data=list(csv.DictReader(labels.open(encoding='utf-8',newline='')))
    if len(data)!=288 or len({(r['window_id'],int(r['target_index'])) for r in data})!=288:
        raise RuntimeError('ORIGINAL_288_ANNOTATION_FRAME_MISMATCH')
    for r in data:
        w=byid.get(r['window_id']);i=int(r['target_index'])
        if w is None or not 0<=i<8 or hashlib.sha256(w['sentences'][i]['sentence_text'].encode()).hexdigest()!=r['text_sha256']:
            raise RuntimeError('ANNOTATION_TARGET_SHA256_MISMATCH')
    det=[r for r in data if r['adjudicated'] in ('0','1')]
    if len(det)!=273:raise RuntimeError('DETERMINATE_REFERENCE_FRAME_MISMATCH')
    invalid=[];counts=[];rows=[];pair=[];rec={}
    for model,slug in MODELS.items():
        if model not in cfg['models']:raise RuntimeError('MODEL_NOT_IN_FROZEN_CONFIG')
        for condition in ('N0','N1'):
            for precision in ('bf16','nf4'):
                folder=results/'E1'/slug/precision/condition
                key=(model,precision,condition);rec[key]={}
                for w in windows:
                    p=folder/(w['window_id']+'.json')
                    if not p.is_file():raise RuntimeError('INCOMPLETE_E1_CHECKPOINTS '+str(p))
                    z=json.loads(p.read_text(encoding='utf-8'))
                    if z.get('window_id')!=w['window_id'] or type(z.get('valid'))!=bool or z.get('raw_sha256')!=sha(z.get('raw','')) or z.get('record_sha256')!=sha(canonical({k:v for k,v in z.items() if k!='record_sha256'})):
                        raise RuntimeError('INVALID_E1_CHECKPOINT '+str(p))
                    rec[key][w['window_id']]=z
                    if not z['valid']:
                        invalid.append({'model':model,'precision':precision,'condition':condition,
                                       'publisher':w['source'],'report_id':w['report_id'],'window_id':w['window_id'],
                                       'error_code':str(z.get('error'))[:160],'raw_sha256':z['raw_sha256'],
                                       'raw_length':len(z['raw']),'generation_cap_reached':z.get('generation_cap_reached')})
                counts.append({'model':model,'precision':precision,'condition':condition,
                               'total_windows':144,'valid_windows':sum(z['valid'] for z in rec[key].values()),
                               'invalid_windows':sum(not z['valid'] for z in rec[key].values())})
        for precision in ('bf16','nf4'):
            a=rec[model,precision,'N0'];b=rec[model,precision,'N1']
            recovered=sum(not a[wid]['valid'] and b[wid]['valid'] for wid in a)
            lost=sum(a[wid]['valid'] and not b[wid]['valid'] for wid in a)
            pair.append({'model':model,'precision':precision,
                         'N0_invalid_N1_valid':recovered,'N0_valid_N1_invalid':lost,
                         'N0_N1_both_valid':sum(a[wid]['valid'] and b[wid]['valid'] for wid in a),
                         'N0_N1_both_invalid':sum(not a[wid]['valid'] and not b[wid]['valid'] for wid in a),
                         'exploratory_unclustered_exact_p':pair_p(recovered,lost)})
        matched_wids={wid for wid in byid if all(rec[model,p,c][wid]['valid'] for p in ('bf16','nf4') for c in ('N0','N1'))}
        for precision in ('bf16','nf4'):
            for condition in ('N0','N1'):
                cell=rec[model,precision,condition]
                def decisions(items):
                    return [(int(r['adjudicated']),int(cell[r['window_id']]['valid'] and int(r['target_index']) in cell[r['window_id']]['indices'])) for r in items]
                itt=f1(decisions(det))
                valid=f1(decisions([r for r in det if cell[r['window_id']]['valid']]))
                paired=f1(decisions([r for r in det if r['window_id'] in matched_wids]))
                rows.append({'model':model,'precision':precision,'condition':condition,
                             'ITT_F1':itt['F1'],'ITT_n':itt['n'],
                             'valid_only_F1':valid['F1'],'valid_only_n':valid['n'],
                             'four_way_matched_F1':paired['F1'],'four_way_matched_n':paired['n'],
                             'four_way_matched_windows_all144':len(matched_wids)})
    out.mkdir(parents=True,exist_ok=True)
    write(out/'E1_invalid_checkpoint_inventory.csv',invalid)
    write(out/'E1_cell_validity.csv',counts)
    write(out/'E1_N0_N1_paired_format_compliance.csv',pair)
    write(out/'E1_ITT_validonly_paired_F1.csv',rows)
    summary={'status':'E1_CPU_INVALIDITY_AND_MATCHED_QUALITY_PASS',
         'total_e1_checkpoints':sum(r['total_windows'] for r in counts),
         'invalid_outputs':len(invalid),'valid_outputs':sum(r['valid_windows'] for r in counts),
         'original_annotated_slots':288,'determinate_labels':273,
         'method':'Intent-to-treat includes invalid outputs as unusable; valid-only denominators differ; four-way-matched F1 uses identical matched labels per model',
         'limitations':'No new GPU inference. Human adjudication is imperfect. Unclustered paired format p-values are exploratory and ignore publisher/report clustering.'}
    (out/'E1_DIAGNOSTIC_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('E1_CPU_INVALIDITY_AND_MATCHED_QUALITY_PASS',json.dumps(summary,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for fld in ('inputs','manifest','results','labels','out'):ap.add_argument('--'+fld,type=Path,required=True)
    a=ap.parse_args();run(a.inputs,a.manifest,a.results,a.labels,a.out)
