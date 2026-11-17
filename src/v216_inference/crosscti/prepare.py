"""Label-blind cross-corpus preparation; rejects fabricated/missing publisher evidence."""
from __future__ import annotations
import argparse,collections,hashlib,json,re
from pathlib import Path
from .core import read,write,write_lines,digest,jdump

def canon(s,cfg):
    if not isinstance(s,str):raise ValueError('MISSING_SOURCE')
    # normalize only case and excess whitespace; do not guess publisher identity
    key=' '.join(s.split()).casefold()
    names={' '.join(x.split()).casefold():x for x in cfg['source_names']}
    if key not in names:raise ValueError('UNKNOWN_PUBLISHER '+repr(s))
    return names[key]

def read_dataset(path,cfg):
    path=Path(path);out=[]
    if path.is_file():
        if path.suffix=='.jsonl':
            with path.open(encoding='utf8') as f:objects=[json.loads(x) for x in f if x.strip()]
        elif path.suffix=='.json':
            o=read(path)
            if isinstance(o,list):objects=o
            elif isinstance(o,dict) and isinstance(o.get('reports'),list):objects=o['reports']
            else:objects=[o]
        else:raise ValueError('EXPECT_JSON_OR_JSONL')
    elif path.is_dir():
        files=sorted([*path.rglob('*.json'),*path.rglob('*.jsonl')]);objects=[]
        if not files:raise ValueError('NO_REPORT_FILES')
        for p in files:
            o=read_dataset(p,cfg);objects.extend(o)
        return objects
    else:raise FileNotFoundError(path)
    for i,o in enumerate(objects):
        if not isinstance(o,dict):raise ValueError('REPORT_NOT_OBJECT')
        c=o.get('CTI')
        if isinstance(c,dict):
            source=c.get('source');txt=c.get('text')
        else:
            source=o.get('source');txt=o.get('text')
        if not isinstance(txt,str) or len(txt.strip())<250:raise ValueError('REPORT_TEXT_TOO_SHORT_OR_MISSING')
        source=canon(source,cfg)
        # ID deliberately based on text+source, independent of local file names and order
        rid=digest([source,txt])[:24]
        out.append({'report_id':rid,'source':source,'text':txt})
    return out

def sentences(text):
    """Conservative deterministic paragraph and sentence splitting, no hidden models."""
    paras=[x.strip() for x in re.split(r'\n\s*\n+',text) if x.strip()]
    s=[]
    for par in paras:
        par=re.sub(r'\s+',' ',par).strip()
        for piece in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"“(])',par):
            piece=piece.strip()
            if 25<=len(piece)<=700 and len(piece.split())>=5:
                s.append(piece)
    return s

def prepare(dataset,root):
    root=Path(root);cfg=read(root/'config/study.json')
    reports=read_dataset(dataset,cfg)
    dsha=hashlib.sha256(Path(dataset).read_bytes()).hexdigest() if Path(dataset).is_file() else None
    if not reports:raise ValueError('EMPTY_DATASET')
    if len({r['report_id'] for r in reports})!=len(reports):raise ValueError('DUPLICATE_REPORT_TEXT')
    # Reject syndicated/reprinted texts across purportedly independent publishers.
    # A source+text ID alone does not detect identical material relabeled under a
    # different publisher. This is a necessary (not sufficient) independence gate.
    cross_source_texts=collections.defaultdict(set)
    normalized_text_counts=collections.Counter()
    for r in reports:
        norm=' '.join(r['text'].split()).casefold()
        fp=hashlib.sha256(norm.encode('utf8')).hexdigest()
        cross_source_texts[fp].add(r['source'])
        normalized_text_counts[fp]+=1
    if any(len(v)>1 for v in cross_source_texts.values()):
        raise ValueError('CROSS_SOURCE_DUPLICATE_TEXT')
    if any(v>1 for v in normalized_text_counts.values()):
        raise ValueError('DUPLICATE_NORMALIZED_REPORT_TEXT')
    by_source=collections.defaultdict(list)
    for r in reports:
        s=sentences(r['text']);r['sentences']=s
        if len(s)>=cfg['min_sentences_per_report']:by_source[r['source']].append(r)
    if len(by_source)!=cfg['min_publishers']:raise ValueError('INSUFFICIENT_PUBLISHER_COVERAGE '+str({k:len(v) for k,v in by_source.items()}))
    for source in cfg['source_names']:
        if len(by_source[source])<cfg['min_reports_per_publisher']:
            raise ValueError('INSUFFICIENT_REPORTS '+source+' '+str(len(by_source[source])))
    selections=[]
    for source in cfg['source_names']:
        candidates=sorted(by_source[source],key=lambda r:digest([cfg['selection_salt'],r['report_id']]))
        selections.extend(candidates[:cfg['target_reports_per_source']])
    windows=[];report_summary=[]
    for r in selections:
        s=r['sentences'];n=len(s);eligible=n//8
        if eligible<2:raise ValueError('INCOMPLETE_REPORT')
        starts=[0,eligible-1] # first and last non-overlapping chunks; deterministic, no labels
        for slot,wi in enumerate(starts):
            batch=s[wi*8:(wi+1)*8]
            # Rotate target ordering by four on alternate window to separate positional preference
            if slot%2:batch=batch[4:]+batch[:4]
            entities=[{'uid':digest([r['report_id'],wi,i,t])[:24],
                       'sentence_text':t,'context_before':''} for i,t in enumerate(batch)]
            w={'window_id':digest([cfg['protocol'],r['report_id'],wi,slot])[:24],
               'report_id':r['report_id'],'source':r['source'],'window_slot':slot,
               'sentences':entities}
            w['input_sha256']=digest(w);windows.append(w)
        report_summary.append({'report_id':r['report_id'],'source':r['source'],'available_sentences':n})
    if len(windows)!=cfg['min_publishers']*cfg['target_reports_per_source']*cfg['windows_per_report']:
        raise ValueError('WINDOW_COUNT_MISMATCH')
    # No labels and no original report corpus serialized in release package
    prepared=root/'outputs/prepared'
    cfgsha=hashlib.sha256((root/'config/study.json').read_bytes()).hexdigest()
    m={'protocol':cfg['protocol'],'dataset_sha256':dsha,'dataset_path_requested':str(dataset),
       'dataset_content_multiset_sha256':digest(sorted([digest([r['source'],r['text']]) for r in reports])),
       'dataset_report_count':len(reports),'publisher_counts_eligible':{k:len(v) for k,v in by_source.items()},
       'selected_reports':report_summary,'windows':len(windows),'calls_per_model_precision':len(windows)*8,
       'total_calls':len(windows)*8*len(cfg['models'])*len(cfg['precisions']),
       'input_sha256':digest((''.join(jdump(w)+'\n' for w in windows)).encode()),
       'config_sha256':cfgsha,'no_gold_labels':True}
    if (root/'outputs/runs').exists() and any((root/'outputs/runs').rglob('*.json')):
        if (prepared/'manifest.json').exists() and read(prepared/'manifest.json')!=m:
            raise RuntimeError('CANNOT_CHANGE_DATASET_AFTER_GPU_RUN')
        if not (prepared/'manifest.json').exists():raise RuntimeError('RUN_EXISTS_WITHOUT_PREPARATION')
    if (prepared/'manifest.json').exists() and read(prepared/'manifest.json')!=m:
        raise RuntimeError('PREPARED_DATASET_DRIFT')
    write_lines(prepared/'inputs.jsonl',windows);write(prepared/'manifest.json',m)
    return m

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--root',default='.')
    a=p.parse_args();print(json.dumps(prepare(a.dataset,a.root),indent=2))
if __name__=='__main__':main()
