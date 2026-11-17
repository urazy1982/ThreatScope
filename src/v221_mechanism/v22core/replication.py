"""Select exactly one fixed v2.1.6 window per publisher for a 432-call environment check.

Produces a pre-inference manifest referencing archived checkpoint identities.
No GPU work is performed here.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from .replay import validate_archive
from .core import digest

def build(archive,seed=20261113):
    cfg,m,windows,rows,audit=validate_archive(archive)
    selection=[]
    for src in cfg['source_names']:
        candidates=[w for w in windows if w['source']==src]
        if len(candidates)!=16:raise RuntimeError('SOURCE_WINDOW_COUNT_NOT_16 '+src)
        key=lambda w:hashlib.sha256((str(seed)+'|'+src+'|'+w['window_id']).encode()).hexdigest()
        w=min(candidates,key=key)
        selection.append({'publisher':src,'report_id':w['report_id'],'window_id':w['window_id'],
          'input_sha256':w['input_sha256']})
    calls=[]
    for model,revision in cfg['models'].items():
        for precision in cfg['precisions']:
            for row in selection:
                for k in range(8):
                    rec=rows[(model,precision,row['window_id'],k)]
                    calls.append({'model':model,'model_revision':revision,'precision':precision,
                       'publisher':row['publisher'],'window_id':row['window_id'],'anchor':k,
                       'archived_record_sha256':rec['record_sha256'],'archived_raw_sha256':rec['raw_sha256'],
                       'archived_valid':rec['valid'],'archived_indices':rec['indices']})
    if len(calls)!=432:raise RuntimeError('BAD_REPLAY_SIZE')
    return {'status':'REPLAY_DESIGN_ONLY_NOT_EXECUTED','design_version':'ThreatStudy-v2.2-Core-draft',
        'random_seed':seed,'baseline_dataset_sha256':m['dataset_sha256'],
        'selected_windows':selection,'calls':calls,'n_calls':len(calls),
        'note':'Do not compare against an old v2.1.6 environment and call it new inference.'}

def compare(manifest,returned):
    """CPU comparator used after true GPU rerun; does not alter archived checkpoint records."""
    expected={(r['model'],r['precision'],r['window_id'],r['anchor']):r for r in manifest['calls']}
    actual={(r['model'],r['precision'],r['window_id'],r['anchor']):r for r in returned}
    if set(actual)!=set(expected):raise RuntimeError('REPLAY_KEYSET_DRIFT')
    counts={'byte_exact':0,'decision_exact':0,'validity_exact':0,'total':len(expected)}
    differences=[]
    for key,orig in expected.items():
        new=actual[key]
        if new.get('revision')!=orig['model_revision']:raise RuntimeError('REVISION_DRIFT')
        byte=new.get('raw_sha256')==orig['archived_raw_sha256']
        decision=new.get('indices')==orig['archived_indices']
        validity=new.get('valid')==orig['archived_valid']
        counts['byte_exact']+=byte;counts['decision_exact']+=decision
        counts['validity_exact']+=validity
        if not(byte and decision and validity):
            differences.append({'key':list(key),'byte_exact':byte,'decision_exact':decision,'validity_exact':validity})
    return {'status':'REPLAY_COMPARED','counts':counts,'differences':differences,
        'arm_A_reuse_for_direct_within_environment_comparison':counts['byte_exact']==counts['total']}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();r=build(a.archive)
    Path(a.out).write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('calls','selected_windows')},indent=2))
