#!/usr/bin/env python3
"""CPU-only E1 v1.1.2 analysis: original 288 labels and 144 matched windows.

Protocol outputs: no duplicate-text label propagation; invalid JSON is a separate
failure category and never a valid empty response. P-values are exploratory.
"""
import argparse
import csv
import hashlib
import itertools
import json
import statistics
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from e1_neutral_gpu import verify_frozen_inputs, PROTOCOL_ID
from audit_e1 import verify_cell
from orchestrate_e1 import MODELS


def f1(tp, fp, fn):
    return 2*tp/(2*tp+fp+fn) if (2*tp+fp+fn) else 0.0

def signflip(vals):
    """Two-sided sign-flip statistic; requires sign exchangeability, NOT assumption-free."""
    if len(vals)<2 or len(vals)>20:return None
    total=abs(sum(vals));tol=1e-12
    return sum(abs(sum(s*v for s,v in zip(signs,vals)))>=total-tol
               for signs in itertools.product((-1,1),repeat=len(vals)))/2**len(vals)

def save_csv(path, rows, columns):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=columns);wr.writeheader();wr.writerows(rows)

def counts_f1(rows):
    tp=sum(r['reference']==1 and r['prediction']==1 for r in rows)
    fp=sum(r['reference']==0 and r['prediction']==1 for r in rows)
    fn=sum(r['reference']==1 and r['prediction']==0 for r in rows)
    tn=sum(r['reference']==0 and r['prediction']==0 for r in rows)
    return tp,fp,fn,tn,f1(tp,fp,fn)

def validate_labels(labels, windows):
    by_id={w['window_id']:w for w in windows}
    if len(labels)!=288:raise RuntimeError('REQUIRES_ORIGINAL_288_LABELS')
    keys=[(r['window_id'],int(r['target_index'])) for r in labels]
    if len(set(keys))!=288 or len({key[0] for key in keys})!=36:
        raise RuntimeError('INVALID_ORIGINAL_SAMPLE_MEMBERSHIP')
    perpub=defaultdict(set);perwin=Counter()
    for r in labels:
        w=by_id.get(r['window_id'])
        if w is None or (r['publisher'],r['report_id'])!=(w['source'],w['report_id']):
            raise RuntimeError('ANNOTATION_SOURCE_ID_MISMATCH')
        index=int(r['target_index'])
        if not 0<=index<8:raise RuntimeError('ANNOTATION_INDEX_OUTSIDE_0_7')
        text=w['sentences'][index]['sentence_text']
        if hashlib.sha256(text.encode('utf-8')).hexdigest()!=r['text_sha256']:
            raise RuntimeError('ANNOTATION_TARGET_TEXT_HASH_MISMATCH')
        if r['adjudicated'] not in ('0','1',''):
            raise RuntimeError('ANNOTATION_LABEL_INVALID')
        perpub[r['publisher']].add(r['report_id']);perwin[r['window_id']]+=1
    if len(perpub)!=9 or any(len(x)!=4 for x in perpub.values()) or set(perwin.values())!={8}:
        raise RuntimeError('SAMPLE_NOT_FOUR_DISTINCT_REPORTS_PER_PUBLISHER_EIGHT_TARGETS')
    if sum(r['adjudicated'] in ('0','1') for r in labels)!=273:
        raise RuntimeError('WRONG_DETERMINATE_COUNT')

def disagreement(xs, ys):
    """Fraction of eight target decisions that disagree; both outputs MUST be valid."""
    return len(set(xs).symmetric_difference(ys))/8


def hierarchical_ci(rows_by_pub, draws=4000, seed=20261114):
    """Descriptive 95% publisher->report bootstrap of a paired window-level effect.

    Report is the sampling unit within a sampled publisher; both report windows
    are kept together. Use publisher-equal aggregation in every bootstrap draw.
    Missing/invalid windows are excluded from the paired effect, never set to 0.
    """
    rng=random.Random(seed)
    pops=sorted(rows_by_pub)
    data={}
    for pub in pops:
        by_report=defaultdict(list)
        for r in rows_by_pub[pub]:
            if r['N1_minus_N0_disagreement_pp'] is not None:
                by_report[r['report_id']].append(r['N1_minus_N0_disagreement_pp'])
        if not by_report:return (None,None,0)
        data[pub]=list(by_report.values())
    samples=[]
    for _ in range(draws):
        pub_means=[]
        for pub in rng.choices(pops,k=len(pops)):
            reports=data[pub]
            selected=rng.choices(reports,k=len(reports))
            vals=[val for report in selected for val in report]
            pub_means.append(statistics.mean(vals))
        samples.append(statistics.mean(pub_means))
    samples.sort()
    return (samples[int(0.025*(draws-1))],samples[int(0.975*(draws-1))],draws)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--results',type=Path,required=True);p.add_argument('--labels',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    manifest,windows,cfg=verify_frozen_inputs(a.inputs,a.manifest)
    labels=list(csv.DictReader(a.labels.open(encoding='utf-8',newline='')))
    validate_labels(labels,windows)
    det=[r for r in labels if r['adjudicated'] in ('0','1')]
    pubs=sorted({w['source'] for w in windows})
    percell={};preds={};audits={};cellrows=[];pubrows=[];diffrows=[]
    mdig=hashlib.sha256(a.manifest.read_bytes()).hexdigest()
    for model,slug in MODELS.items():
        for condition in ('N0','N1'):
            for precision in ('bf16','nf4'):
                folder=a.results/'E1'/slug/precision/condition
                audit=verify_cell(folder,model,precision,condition,windows,manifest,cfg,144,mdig)
                rec={w['window_id']:json.loads((folder/(w['window_id']+'.json')).read_text()) for w in windows}
                preds[(model,condition,precision)]=rec;audits[(model,condition,precision)]=audit
                vectors=[{'publisher':r['publisher'],'reference':int(r['adjudicated']),
                          'prediction':int(rec[r['window_id']]['valid'] and int(r['target_index']) in rec[r['window_id']]['indices']),
                          'window_id':r['window_id']} for r in det]
                percell[(model,condition,precision)]=vectors
                tp,fp,fn,tn,pooled=counts_f1(vectors)
                samplewin={r['window_id'] for r in det}
                cellrows.append(dict(model=model,precision=precision,condition=condition,
                    valid_windows=audit['valid'],invalid_windows=audit['invalid'],total_windows=144,
                    sample_determinate_n=273,sample_invalid_windows=sum(not rec[wid]['valid'] for wid in samplewin),
                    TP=tp,FP=fp,FN=fn,TN=tn,pooled_F1=pooled,
                    pooled_accuracy=(tp+tn)/len(vectors),
                    valid_empty_fraction=audit['valid_empty_fraction'],
                    valid_empty_windows=audit['valid_empty_windows'],
                    mean_selected_given_valid=audit['mean_selected_given_valid'],
                    mean_usable_selected_per_window=audit['mean_usable_selected_per_window'],
                    generation_cap_reached=audit['generation_cap_reached']))
                for pub in pubs:
                    z=[r for r in vectors if r['publisher']==pub]
                    tp,fp,fn,tn,score=counts_f1(z)
                    pubrows.append(dict(model=model,precision=precision,condition=condition,
                                        publisher=pub,n=len(z),TP=tp,FP=fp,FN=fn,TN=tn,F1=score))
            for pub in pubs:
                q={(r['model'],r['precision'],r['condition'],r['publisher']):r for r in pubrows}
                a0=q[(model,'bf16',condition,pub)]['F1'];a1=q[(model,'nf4',condition,pub)]['F1']
                diffrows.append(dict(model=model,condition=condition,publisher=pub,
                                     delta_F1_pp=(a1-a0)*100))
    summary=[];prompt_contrasts=[];interaction=[]
    pub_lookup={(r['model'],r['precision'],r['condition'],r['publisher']):r for r in pubrows}
    for model in MODELS:
        for condition in ('N0','N1'):
            diffs=[r['delta_F1_pp'] for r in diffrows if r['model']==model and r['condition']==condition]
            summary.append(dict(model=model,condition=condition,publisher_equal_delta_F1_pp=statistics.mean(diffs),
                 exact_signflip_p=signflip(diffs),publishers=len(diffs),
                 positive_publishers=sum(v>0 for v in diffs),negative_publishers=sum(v<0 for v in diffs),
                 note='Exploratory original 288-slot human-reference F1; no multiple-test adjustment'))
        for precision in ('bf16','nf4'):
            diffs=[]
            for pub in pubs:
                n0=pub_lookup[(model,precision,'N0',pub)]['F1'];n1=pub_lookup[(model,precision,'N1',pub)]['F1']
                diffs.append((n1-n0)*100)
            prompt_contrasts.append(dict(model=model,precision=precision,contrast='N1_minus_N0_F1',
                publisher_equal_delta_F1_pp=statistics.mean(diffs),publisher_signflip_p=signflip(diffs),
                positive_publishers=sum(v>0 for v in diffs),negative_publishers=sum(v<0 for v in diffs)))
    # Difference-in-differences of F1 at publisher level (exploratory, adjudication-limited).
    for model in MODELS:
        vals=[]
        for pub in pubs:
            def score(prec,cond):return pub_lookup[(model,prec,cond,pub)]['F1']
            val=100*((score('nf4','N1')-score('bf16','N1'))-(score('nf4','N0')-score('bf16','N0')))
            vals.append(val)
        interaction.append(dict(model=model,estimand='F1_NF4_minus_BF16_difference_of_N1_minus_N0',
            publisher_equal_DID_pp=statistics.mean(vals),exact_signflip_p=signflip(vals),
            positive_publishers=sum(v>0 for v in vals),negative_publishers=sum(v<0 for v in vals),
            note='Exploratory human-reference precision-by-prompt interaction; not Arm A index sensitivity'))
    # The central mitigation estimand is a *direct*, paired, precision-discordance
    # contrast between N1 and N0 on the same 144 windows. Invalid predictions
    # are missing for this metric rather than misidentified as empty selections.
    stability_win=[];stability_pub=[];stability_summary=[]
    for model in MODELS:
        rows_by_pub=defaultdict(list)
        for w in windows:
            wid=w['window_id'];records={}
            for c in ('N0','N1'):
                for p in ('bf16','nf4'):
                    records[(c,p)]=preds[(model,c,p)][wid]
            v0=records['N0','bf16']['valid'] and records['N0','nf4']['valid']
            v1=records['N1','bf16']['valid'] and records['N1','nf4']['valid']
            d0=disagreement(records['N0','bf16']['indices'],records['N0','nf4']['indices']) if v0 else None
            d1=disagreement(records['N1','bf16']['indices'],records['N1','nf4']['indices']) if v1 else None
            row=dict(model=model,publisher=w['source'],report_id=w['report_id'],window_id=wid,
                     N0_both_valid=int(v0),N1_both_valid=int(v1),all_four_valid=int(v0 and v1),
                     N0_precision_disagreement=d0,N1_precision_disagreement=d1,
                     N1_minus_N0_disagreement_pp=(d1-d0)*100 if (v0 and v1) else None)
            stability_win.append(row);rows_by_pub[w['source']].append(row)
        effects=[];valids=0
        for pub in pubs:
            rows=rows_by_pub[pub]
            matched=[r['N1_minus_N0_disagreement_pp'] for r in rows if r['all_four_valid']]
            valid_n=len(matched);valids+=valid_n
            effect=statistics.mean(matched) if matched else None
            if effect is not None:effects.append(effect)
            stability_pub.append(dict(model=model,publisher=pub,windows=len(rows),
                 all_four_valid_windows=valid_n,valid_fraction=valid_n/len(rows),
                 mean_N1_minus_N0_disagreement_pp=effect))
        balanced=(len(effects)==9 and valids==144)
        lower,upper,draws=hierarchical_ci(rows_by_pub) if len(effects)==9 else (None,None,0)
        stability_summary.append(dict(model=model,estimand='paired_N1_minus_N0_cross_precision_disagreement',
              matched_windows=valids,total_windows=144,matched_fraction=valids/144,
              publishers_with_complete_cases=len(effects),
              publisher_equal_effect_pp=statistics.mean(effects) if len(effects)==9 else None,
              exact_p_exploratory=signflip(effects) if len(effects)==9 else None,
              descriptive_bootstrap_CI95_low_pp=lower,descriptive_bootstrap_CI95_high_pp=upper,bootstrap_draws=draws,
              validity_gate='ALL_WINDOWS_VALID' if balanced else 'INCOMPLETE_MATCHING_INTERPRET_CAUTIOUSLY',
              note='Lower disagreement is not automatically better: check empty output and F1 guardrails.'))
    # Three-model primary-family multiplicity: Holm correction (only for
    # directly specified E1 stability contrasts, not every secondary test).
    observed=sorted((r for r in stability_summary if r['exact_p_exploratory'] is not None),
                    key=lambda r:r['exact_p_exploratory'])
    running=0.0;count=len(observed)
    for rank,row in enumerate(observed):
        running=max(running,min(1.0,row['exact_p_exploratory']*(count-rank)))
        row['holm3_primary_p']=running if count==3 else None
    for row in stability_summary:
        if 'holm3_primary_p' not in row:row['holm3_primary_p']=None
    out=a.out;out.mkdir(parents=True,exist_ok=True)
    for fn,rs in [('E1_cell_quality.csv',cellrows),('E1_publisher_quality.csv',pubrows),
                  ('E1_publisher_precision_deltas.csv',diffrows),('E1_summary.csv',summary),
                  ('E1_prompt_F1_contrasts.csv',prompt_contrasts),('E1_F1_interaction_DID.csv',interaction),('E1_stability_window.csv',stability_win),
                  ('E1_stability_publisher.csv',stability_pub),('E1_stability_summary.csv',stability_summary)]:
        save_csv(out/fn,rs,list(rs[0]))
    (out/'E1_ANALYSIS_LIMITATIONS.md').write_text('''# ThreatScope v1.1.2 E1 interpretation\n\nThe central direct control contrast is paired within-window N1 minus N0 precision-discordance (symmetric difference of eight binary target decisions), conditional on all four corresponding outputs being valid; four-way validity/coverage is explicitly reported. Invalid outputs are a separate outcome and MUST NOT be counted as valid empty selections. The original human reference evaluation uses 288 sampled slots (273 determinate), not 371 propagated duplicates; invalid JSON counts as an unusable extraction in intent-to-treat F1, with validity shown separately. Human adjudication is imperfect and not a definitive expert ground truth. An empty-list exemplar can trivially improve apparent precision agreement by suppressing selection; output cardinality, valid empty rate, and human-reference F1 are therefore essential guardrails.\n\nN0/N1 differ only by the optional appended empty JSON example, using the same target serialization and historical Arm A system instruction. They do not directly estimate the original eight-anchor index sensitivity, and Arm A vs E1 changes prompt content and experimental chronology. All inferential tests are exploratory and unadjusted; publisher sign-flips assume sign exchangeability, n=9. The preselected 144 windows are not externally independent reports, so E1 cannot establish generalization.\n''',encoding='utf-8')
    print('E1_CPU_POSTANALYSIS_PASS',len(cellrows),'cells',len(pubrows),'publisher rows',len(stability_summary),'direct paired stability contrasts')
if __name__=='__main__':main()
