"""Compare uploaded real CPU gate, tokenizer preflight, and 6912 GPU input-token records."""
from __future__ import annotations
import collections,hashlib,json,statistics
from pathlib import Path
from .replay import validate_archive

def audit(archive,final_gate,preflight):
    cfg,m,windows,rows,checks=validate_archive(archive)
    gate=json.loads(Path(final_gate).read_text())
    tok=json.loads(Path(preflight).read_text())
    if gate['dataset_sha256']!=m['dataset_sha256'] or gate['input_sha256']!=m['input_sha256']:
        raise RuntimeError('FINAL_CPU_GATE_FINGERPRINT_DISAGREES')
    if gate.get('exact_overlap_full_apt_vs_smah_windows')!=0 or gate.get('near_duplicate_flag_count')!=0:
        raise RuntimeError('FINAL_CPU_GATE_UNRESOLVED_OVERLAP')
    if gate['reports']!=72 or gate['windows']!=144 or any(x!=8 for x in gate['source_counts'].values()):
        raise RuntimeError('FINAL_CPU_GATE_UNBALANCED')
    if gate['source_revision']!=cfg['source_release_revision'] or gate['source_metadata_sha256']!=cfg['source_release_index_sha256']:
        raise RuntimeError('FINAL_CPU_GATE_SOURCE_IDENTITY_DISAGREES')
    tk={x['model']:x for x in tok}
    result=[]
    for model in cfg['models']:
        lengths=collections.defaultdict(list);max_tokens=0;bad_windows=0
        latency={p:[] for p in cfg['precisions']};gen={p:[] for p in cfg['precisions']}
        cap={p:0 for p in cfg['precisions']}
        for w in windows:
            for precision in cfg['precisions']:
                lx=[]
                for e in range(8):
                    rec=rows[(model,precision,w['window_id'],e)]
                    lx.append(rec['input_tokens']);latency[precision].append(rec['latency_seconds'])
                    gen[precision].append(rec['generated_tokens']);cap[precision]+=int(rec['generation_cap_reached'])
                if len(set(lx))!=1:bad_windows+=1
                max_tokens=max(max_tokens,max(lx))
        if bad_windows or tk[model]['unequal_windows']!=0 or not tk[model]['ok']:
            raise RuntimeError('ANCHOR_TOKEN_LENGTH_DRIFT '+model)
        if max_tokens!=tk[model]['max_input_tokens']:
            raise RuntimeError('PREFLIGHT_MAX_TOKEN_MISMATCH '+model+' '+str((max_tokens,tk[model]['max_input_tokens'])))
        result.append({'model':model,'actual_archived_max_input_tokens':max_tokens,
            'preflight_report_max_input_tokens':tk[model]['max_input_tokens'],
            'prompt_token_length_disagreements':bad_windows,'precisions':{
                p:{'mean_latency_seconds':statistics.mean(latency[p]),
                    'sum_latency_seconds':sum(latency[p]),
                    'mean_generated_tokens':statistics.mean(gen[p]),
                    'capped_generations':cap[p]} for p in cfg['precisions']}})
    return {'status':'REFERENCE_PROVENANCE_AND_TOKEN_COUNTS_PASS',
       'source_revision':cfg['source_release_revision'],'dataset_sha256':m['dataset_sha256'],
       'source_metadata_sha256':cfg['source_release_index_sha256'],
       'readiness':'REFERENCE_ARCHIVE_VERIFIED; V2.2 B/C TOKENIZERS AND GPU OUTPUTS NOT RUN',
       'limitations':gate['limitations'], 'models':result}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--archive',required=True);p.add_argument('--final-gate',required=True)
    p.add_argument('--preflight',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();result=audit(a.archive,a.final_gate,a.preflight)
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
