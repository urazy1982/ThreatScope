"""Read-only final scientific CPU gate for a staged APT workspace.

No GPU execution is enabled by this tool. Near-duplicates are flagged for review,
not automatically classified as independent evidence.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re
from pathlib import Path
from urllib.parse import urlparse
from .analyze import verify_prepared
from .core import lines


def hash_file(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def norm(s):return ' '.join(s.split()).casefold()
def grams(s,n=5):
    words=re.findall(r'[a-z0-9]+',s.casefold())
    return {tuple(words[i:i+n]) for i in range(max(0,len(words)-n+1))}

def source_host(url,source):
    from corpusapt.acquire import matches_host
    return matches_host(url,source)

def validate(root,smah,preflight=None):
    root=Path(root)
    cfg,manifest,windows=verify_prepared(root)
    prov_path=root/'dataset/corpus_provenance.json'
    report_path=root/'dataset/reports.json'
    if not prov_path.is_file() or not report_path.is_file():
        raise RuntimeError('MISSING_ARTICLE_PROVENANCE')
    prov=json.loads(prov_path.read_text())
    reports=json.loads(report_path.read_text())
    if len(reports)!=72 or len(windows)!=144 or manifest['total_calls']!=6912:raise RuntimeError('DESIGN_COUNT_DRIFT')
    if len(cfg['source_names'])!=9 or set(cfg['source_names'])!={r['source'] for r in reports}:raise RuntimeError('PUBLISHER_SET_DRIFT')
    if collections.Counter(r['source'] for r in reports)!={s:8 for s in cfg['source_names']}:raise RuntimeError('PUBLISHER_BALANCE_DRIFT')
    if prov.get('overlap_repair_status')!='FULL_REPORT_SENTENCE_EXCLUSION_PASS' or not prov.get('smah_inputs_sha256'):
        raise RuntimeError('MISSING_OVERLAP_REPAIR_ATTESTATION')
    if prov.get('revision') != cfg.get('source_release_revision') or prov.get('index_sha256') != cfg.get('source_release_index_sha256'):
        raise RuntimeError('PUBLISHER_INDEX_REVISION_DRIFT')
    if len(prov.get('records',[]))!=72:raise RuntimeError('PROVENANCE_RECORD_COUNT_DRIFT')
    if manifest['dataset_sha256']!=hash_file(report_path):raise RuntimeError('REPORT_DATASET_HASH_DRIFT')
    if prov['smah_inputs_sha256']!=hash_file(smah):raise RuntimeError('SMAH_BASELINE_CHANGED')
    seen=set()
    from corpusapt.acquire import sha
    for r,record in zip(reports,prov['records']):
        if r['source']!=record['source'] or r['url']!=record['url'] or r['archive_path']!=record['archive_path']:
            raise RuntimeError('PROVENANCE_RECORD_MISMATCH')
        if not source_host(r['url'],r['source']):raise RuntimeError('PUBLISHER_HOST_MISMATCH')
        if r['html_sha256']!=record['html_sha256']:raise RuntimeError('ARTICLE_HASH_MISMATCH')
        if sha(r['text'].encode('utf-8'))!=record['text_sha256']:raise RuntimeError('ARTICLE_TEXT_HASH_MISMATCH')
        if r['url'] in seen:raise RuntimeError('REPEATED_URL')
        seen.add(r['url'])
    from .prepare import sentences
    old=lines(smah)
    baseline={norm(s.get('sentence_text',s.get('target',''))) for w in old for s in w['sentences']}
    baseline.discard('')
    if not baseline:raise RuntimeError('EMPTY_BASELINE')
    overlap=[(r['source'],r['url'],s) for r in reports for s in sentences(r['text']) if norm(s) in baseline]
    if overlap:raise RuntimeError('REPAIRED_REPORT_EXACT_OVERLAP '+str(len(overlap)))
    # Truncated baseline windows cannot certify full-report independence.
    # Screen distinct, fairly long passages; short boilerplate should not be
    # treated as conclusive reuse of an entire report.
    old_strings=[' '.join(s.get('sentence_text',s.get('target','')) for s in w['sentences']) for w in old]
    old_shingles=[grams(x) for x in old_strings]
    similar=[]
    for r in reports:
        g=grams(r['text'])
        for i,h in enumerate(old_shingles):
            if len(h)<30:continue
            shared=len(h&g)
            containment=shared/len(h)
            if containment >= 0.65 and shared >= 25:
                similar.append({'source':r['source'],'url':r['url'],'baseline_window_index':i,
                                'baseline_window_containment':round(containment,5),
                                'matching_5grams':shared})
    # A safe attestation requires preflight results tied explicitly to the exact
    # manifest; the old v2.1.4 JSON has no such identifiers, so it is informative
    # but cannot be considered proof tied to a specific prepared sample.
    pstatus='NOT_PROVIDED';pcounts={}
    if preflight:
        arr=json.loads(Path(preflight).read_text())
        if not isinstance(arr,list) or {r['model'] for r in arr}!=set(cfg['models']):
            raise RuntimeError('PREFLIGHT_MODEL_SET_MISMATCH')
        for x in arr:
            if x.get('ok') is not True or x.get('unequal_windows')!=0 or not (64<=x.get('max_input_tokens',0)<=cfg['max_input_tokens']):
                raise RuntimeError('TOKENIZER_PREFLIGHT_INVALID')
            pcounts[x['model']]=x['max_input_tokens']
        pstatus='PASS_UNBOUND_TO_DATASET_USE_AS_SUPPORTING_EVIDENCE'
    report={
        'status':'CPU_AUDIT_PASS_WITH_NEAR_DUP_REVIEW' if similar else 'CPU_AUDIT_PASS_NEAR_DUP_SCREEN_ONLY',
        'dataset_sha256':manifest['dataset_sha256'],
        'input_sha256':manifest['input_sha256'],
        'config_sha256':manifest['config_sha256'],
        'source_revision':prov['revision'],
        'source_metadata_sha256':prov['index_sha256'],
        'archive_sha256':prov['archive_sha256'],
        'smah_sha256':prov['smah_inputs_sha256'],
        'source_counts':dict(collections.Counter(r['source'] for r in reports)),
        'reports':len(reports),'windows':len(windows),'gpu_calls_planned':manifest['total_calls'],
        'exact_overlap_full_apt_vs_smah_windows':len(overlap),
        'near_duplicate_flags':similar[:150],
        'near_duplicate_flag_count':len(similar),
        'tokenizer_preflight':pstatus,'max_input_tokens':pcounts,
        'limitations':['SMAH baseline contains only selected windows, not original full reports',
                       'Near-duplicate shingle screen is not definitive semantic identity evidence',
                       'Preflight v2.1.4 output lacks dataset-bound checksum and cannot alone authorize GPU',
                       'GPU gate remains CLOSED in v2.1.4/v2.1.5'],
        'gpu_gate':'CLOSED_PENDING_FINAL_REVIEW'
    }
    return report

def main():
    a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--smah-inputs',required=True)
    a.add_argument('--preflight');a.add_argument('--out',required=True)
    p=a.parse_args();result=validate(p.root,p.smah_inputs,p.preflight)
    path=Path(p.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='near_duplicate_flags'},indent=2))
if __name__=='__main__':main()
