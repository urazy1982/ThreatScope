"""CPU-only, provenance-gated staging for CZLi/apt-reports.

The source texts remain local and are not included in the source-code release.
Never infer a publisher merely from a filename or an unrelated page title.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, shutil, tempfile, zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

REPO_ID = 'CZLi/apt-reports'
ARCHIVE = 'apt_github_distribution_20260922T211548298793Z.zip'
INDEX_FILES = ('filename_map.json', 'classifications.json', 'source_risks.json', 'README.md', 'LICENSE')
SALT = 'ThreatStudy-APT-Publisher-20261113-v2.1.1-NINE-SOURCE-pre-inference'
REPAIR_PROTOCOL = 'threatstudy-aptpublisher-balance-v2.1.4-overlap-repair-20261113'
# Frozen, pre-outcome source order. Skip high-risk Microsoft/Sekoia and non-English CERT-UA.
CANDIDATES = (
    'securelist_apt', 'eset_apt_reports', 'thehackernews_apt',
    'trendmicro_apt', 'unit42_apt', 'bitdefender_apt',
    'talos_apt', 'groupib_apt', 'volexity_apt', 'sentinellabs_apt',
    'asec_apt', 'sophos_pacific_rim',
)
HOSTS = {
    'securelist_apt': ('securelist.com',),
    'eset_apt_reports': ('welivesecurity.com',),
    'thehackernews_apt': ('thehackernews.com',),
    'trendmicro_apt': ('trendmicro.com',),
    'unit42_apt': ('paloaltonetworks.com',),
    'bitdefender_apt': ('bitdefender.com',),
    'talos_apt': ('talosintelligence.com',),
    'groupib_apt': ('group-ib.com',),
    'volexity_apt': ('volexity.com',),
    'sentinellabs_apt': ('sentinelone.com',),
    'asec_apt': ('ahnlab.com',),
    'sophos_pacific_rim': ('sophos.com',),
}
NUM_KEYS = ('article_number', 'article_no', 'number', 'new_number', 'num', 'file_number', 'id')
URL_KEYS = ('url', 'article_url', 'original_url', 'source_url', 'link')
SOURCE_KEYS = ('source', 'source_id', 'publisher', 'publisher_id', 'site', 'source_name')
PATH_KEYS = ('archive_path', 'archive_html_path', 'html_path', 'html_file', 'file', 'filename', 'new_filename', 'path')


def sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def save(p, data):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)+'\n', encoding='utf-8')


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def revision_check(s: str) -> bool:
    return bool(re.fullmatch(r'[a-f0-9]{40}', s))


def fetch_indexes(dest: Path, revision: str | None = None):
    """Download ONLY small public metadata; pin the repository commit."""
    try:
        from huggingface_hub import HfApi, hf_hub_download
    except ImportError as ex:
        raise RuntimeError('MISSING_DEPENDENCY: pip install huggingface_hub') from ex
    if revision is None:
        revision = HfApi().dataset_info(REPO_ID).sha
    if not revision_check(revision):
        raise RuntimeError('INVALID_DATASET_REVISION '+str(revision))
    dest = Path(dest); dest.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in INDEX_FILES:
        remote = Path(hf_hub_download(REPO_ID, filename=name, repo_type='dataset', revision=revision))
        target = dest/name
        if target.exists() and sha(target.read_bytes()) != sha(remote.read_bytes()):
            raise RuntimeError('INDEX_CONTENT_CHANGED '+name)
        if not target.exists():shutil.copyfile(remote, target)
        files[name] = dict(sha256=sha(target.read_bytes()), bytes=target.stat().st_size)
    provenance = {'repo_id':REPO_ID,'revision':revision,'files':files,
                  'archive':ARCHIVE, 'source_catalog': 'peng-gao-lab/cti-crawler',
                  'candidate_order':list(CANDIDATES), 'downloaded_real_metadata':True}
    save(dest/'provenance.json', provenance)
    return provenance


def checked_index(meta: Path):
    p = load(meta/'provenance.json')
    if p.get('repo_id') != REPO_ID or not revision_check(p.get('revision', '')):
        raise RuntimeError('INVALID_INDEX_PROVENANCE')
    for name, rec in p['files'].items():
        f = meta/name
        if not f.is_file() or sha(f.read_bytes()) != rec['sha256']:
            raise RuntimeError('INDEX_SHA_MISMATCH '+name)
    return p


def first(obj, names):
    return next((obj[k] for k in names if k in obj and obj[k] is not None), None)


def number_from(obj, hint=None):
    vals = [first(obj, NUM_KEYS), first(obj, PATH_KEYS), hint]
    for value in vals:
        if isinstance(value, int) and 0 <= value <= 999999: return f'{value:06d}'
        if isinstance(value, str):
            value = value.strip()
            if re.fullmatch(r'\d{1,6}',value): return value.zfill(6)
            match = re.search(r'(?:^|/)(\d{6})\.(?:html|pdf)(?:$|\?)', value,flags=re.I)
            if match:return match.group(1)
    return None


def matches_host(url, source):
    if source not in HOSTS or not isinstance(url, str): return False
    u=urlparse(url)
    if u.scheme not in ('https','http') or not u.hostname: return False
    host=u.hostname.lower().rstrip('.')
    return any(host==suffix or host.endswith('.'+suffix) for suffix in HOSTS[source])


def index_records(index):
    """Extract only source-linked URL/article records with external-site verification.

    The source may be a key in a publisher-index hierarchy but is never
    inferred from an arbitrary filename or the URL hostname alone.
    """
    records=[];seen=set();walked=0
    def walk(obj,hint=None,depth=0,inherited_source=None,inherited_url=None):
        nonlocal walked
        if depth>14: raise RuntimeError('INDEX_NESTING_LIMIT')
        walked+=1
        if walked>150000: raise RuntimeError('INDEX_SIZE_LIMIT')
        if isinstance(obj,list):
            for x in obj:walk(x,None,depth+1,inherited_source,inherited_url)
        elif isinstance(obj,dict):
            source=first(obj,SOURCE_KEYS) or (hint if hint in HOSTS else inherited_source)
            url=first(obj,URL_KEYS) or (hint if isinstance(hint,str) and hint.startswith(('http://','https://')) else inherited_url)
            num=number_from(obj,hint)
            if isinstance(source,str) and isinstance(url,str) and num:
                src=source.strip()
                if src in HOSTS and matches_host(url,src) and obj.get('included') is not False:
                    key=(src,num,url)
                    if key not in seen: records.append({'source':src,'number':num,'url':url});seen.add(key)
            for k,v in obj.items():
                if isinstance(v,(dict,list)):walk(v,k,depth+1,source,url)
    walk(index)
    return records


def summarize_index(meta):
    meta=Path(meta);p=checked_index(meta)
    raw=load(meta/'filename_map.json')
    records=index_records(raw)
    counts=collections.Counter(r['source'] for r in records)
    # Small schema preview to diagnose upstream format changes without dumping
    # the multi-megabyte index or any report text into the user-facing summary.
    cursor=raw
    for _ in range(4):
        if isinstance(cursor,list) and cursor:cursor=cursor[0]
        elif isinstance(cursor,dict) and cursor:cursor=next(iter(cursor.values()))
        else:break
    preview=json.dumps(cursor,ensure_ascii=False,default=str)[:900]
    info={
        'data_source':REPO_ID,'revision':p['revision'],
        'root_type':type(raw).__name__,
        'root_keys':list(raw)[:15] if isinstance(raw,dict) else None,
        'schema_preview':preview,
        'record_count_verified':len(records),
        'source_counts':{s:counts[s] for s in CANDIDATES},
        'eligible_sources_with_8_indexed':sum(counts[s]>=8 for s in CANDIDATES),
        'candidate_order':list(CANDIDATES),
        'first_verified_record':records[0] if records else None,
        'metadata_sha256':p['files']['filename_map.json']['sha256'],
        'gate_pass':sum(counts[s]>=8 for s in CANDIDATES)>=10,
        'reason':None if records else 'UNRECOGNIZED_INDEX_SCHEMA_OR_NO_VERIFIABLE_RECORDS',
    }
    save(meta/'source_inventory.json',info)
    return info


def archive_path_parts(name):
    name = name.replace('\\','/')
    if name.startswith('/') or any(x=='..' for x in PurePosixPath(name).parts):
        return None
    m=re.search(r'(?:^|/)02_APT_publishers/([a-z0-9_]+)/html/(\d{6})\.html$',name)
    return (m.group(1),m.group(2)) if m else None


def html_text(data):
    """Offline extraction; preserve paragraph boundaries for frozen splitter."""
    try:
        from bs4 import BeautifulSoup
    except ImportError as ex:raise RuntimeError('MISSING_DEPENDENCY: pip install beautifulsoup4 lxml') from ex
    soup=BeautifulSoup(data,'lxml')
    for tag in soup(['script','style','noscript','svg','iframe','form','nav','footer']):tag.decompose()
    element=soup.find('article') or soup.find('main') or soup.body or soup
    texts=[]
    for el in element.find_all(['p','li','h2','h3']):
        if el.find_parent(['p','li','h2','h3']) is not None:continue
        val=' '.join(el.get_text(' ',strip=True).split())
        if len(val)>=40:texts.append(val)
    if not texts:
        val=element.get_text(' ',strip=True)
        texts=[val] if val else []
    return '\n\n'.join(texts)


def high_overlap(text_a,text_b):
    """Jaccard of 5-word shingles for duplicate-warning gate, not a label."""
    def grams(s):
        w=re.findall(r'[a-z0-9]+',s.casefold())
        return {tuple(w[i:i+5]) for i in range(len(w)-4)}
    a=grams(text_a);b=grams(text_b)
    return len(a&b)/len(a|b) if a and b else 0.0


def stage_archive(meta: Path, archive: Path, workspace: Path, base_study: Path, smah_inputs: Path | None = None):
    """Read original ZIP without extracting all 10.7 GB; freeze 80 records locally."""
    from crosscti.prepare import sentences,prepare
    meta=Path(meta);workspace=Path(workspace);archive=Path(archive)
    p=checked_index(meta)
    inv=summarize_index(meta)
    if not inv['gate_pass']:
        raise RuntimeError('INDEX_SOURCE_COVERAGE_GATE_FAIL: inspect source_inventory.json first')
    if not archive.is_file():raise FileNotFoundError(archive)
    if not zipfile.is_zipfile(archive):raise RuntimeError('ARCHIVE_NOT_A_ZIP')
    if (workspace/'outputs/runs').exists():raise RuntimeError('EXISTING_GPU_OUTPUTS_NOT_ALLOWED')
    index=index_records(load(meta/'filename_map.json'))
    bykey=collections.defaultdict(list)
    for x in index:bykey[(x['source'],x['number'])].append(x)
    selection=collections.defaultdict(list)
    count=collections.Counter()
    with zipfile.ZipFile(archive) as z:
        candidates=[]
        for zi in z.infolist():
            pair=archive_path_parts(zi.filename)
            if pair and pair[0] in HOSTS:
                candidates.append((pair,zi))
        count['html_entries_in_zip'] = len(candidates)
        for (src,num),zi in sorted(candidates,key=lambda x:(CANDIDATES.index(x[0][0]) if x[0][0] in CANDIDATES else 99,x[0][1])):
            recs=bykey.get((src,num),[])
            if len(recs)!=1:
                count['missing_or_ambiguous_index_link']+=1;continue
            rec=recs[0]
            if zi.file_size>8_000_000:
                count['html_over_size_limit']+=1;continue
            data=z.read(zi)
            text=html_text(data)
            if len(text)<1400 or len(text.split())<200 or len(sentences(text))<16:
                count['html_too_short_or_low_sentence_coverage']+=1;continue
            selection[src].append({'source':src,'text':text,'number':num,'url':rec['url'],
                                   'zip_path':zi.filename,'html_sha256':sha(data),
                                   'text_sha256':sha(text.encode('utf-8'))})
    qualified=[s for s in CANDIDATES if len(selection[s])>=8]
    if len(qualified)<9:
        details={s:len(selection[s]) for s in CANDIDATES}
        save(meta/'real_content_eligibility.json',{'status':'FAIL','counts':details,'other':dict(count)})
        raise RuntimeError('REAL_CONTENT_SOURCE_COVERAGE_FAIL '+str(details))
    chosen=qualified[:9]
    # A matched-window exact-sentence exclusion is a data-independence intervention, not an outcome filter.
    # Preserve the pre-outcome selection order; take the next eligible source report if an earlier one overlaps.
    from crosscti.core import lines, digest
    baseline=set()
    source_rows=[]
    if smah_inputs is not None:
        smah_inputs=Path(smah_inputs)
        if not smah_inputs.is_file():raise FileNotFoundError(smah_inputs)
        source_rows=lines(smah_inputs)
        if not source_rows:raise RuntimeError('SMAH_BASELINE_EMPTY')
    def normalize_sentence(v):return ' '.join(v.split()).casefold()
    for w in source_rows:
        for obj in w.get('sentences',[]):
            t=obj.get('sentence_text',obj.get('target',''))
            if isinstance(t,str) and t.strip():baseline.add(normalize_sentence(t))
    if smah_inputs is not None and not baseline:raise RuntimeError('SMAH_BASELINE_NO_SENTENCES')
    selected=[];full_counts={s:len(selection[s]) for s in CANDIDATES}
    excluded=[]
    for source in chosen:
        pool=sorted(selection[source],key=lambda r:sha((SALT+'|'+source+'|'+r['url']).encode()))
        accepted=0
        for r in pool:
            shared=sorted({normalize_sentence(t) for t in sentences(r['text']) if normalize_sentence(t) in baseline})
            if shared:
                excluded.append({'source':source,'number':r['number'],'url':r['url'],
                                 'report_id':digest([source,r['text']])[:24],
                                 'overlap_count':len(shared),
                                 'shared_sentence_sha256':[sha(x.encode('utf-8')) for x in shared]})
                continue
            selected.append(r);accepted+=1
            if accepted==8:break
        if accepted!=8:
            raise RuntimeError('NO_EIGHT_NONOVERLAPPING_REPORTS '+source+' '+str(accepted))
    if len(selected)!=72:raise RuntimeError('SAMPLE_SIZE_MISMATCH')
    if len({r['url'] for r in selected})!=72:raise RuntimeError('DUPLICATE_URL_BEFORE_PREPARE')
    if any(normalize_sentence(t) in baseline for r in selected for t in sentences(r['text'])):
        raise RuntimeError('OVERLAP_REPAIR_POSTCONDITION_FAIL')
    # Dedup in the frozen sample: exact and near-duplicate text, plus reused URLs.
    normalized={};seenurl=set();warnings=[]
    for r in selected:
        key=' '.join(r['text'].split()).casefold()
        if key in normalized:raise RuntimeError('DUPLICATE_SELECTED_TEXT '+r['url'])
        normalized[key]=r['url']
        u=r['url'].rstrip('/').casefold()
        if u in seenurl:raise RuntimeError('REPEATED_URL')
        seenurl.add(u)
    # Precompute shingles: quadratic comparison in 80 reports, linear parsing.
    def shingle(s):
        words=re.findall(r'[a-z0-9]+',s.casefold())
        return {tuple(words[i:i+5]) for i in range(len(words)-4)}
    grams=[shingle(r['text']) for r in selected]
    for i,a in enumerate(selected):
        for j in range(i+1,len(selected)):
            x,y=grams[i],grams[j]
            if x and y and len(x & y)/len(x | y)>=0.85:
                b=selected[j]
                warnings.append({'url_a':a['url'],'url_b':b['url'],'sources':[a['source'],b['source']]})
    if warnings:
        save(meta/'near_duplicate_review_required.json',warnings)
        raise RuntimeError('NEAR_DUPLICATE_REVIEW_REQUIRED '+str(len(warnings)))
    workspace.mkdir(parents=True,exist_ok=True)
    src=Path(base_study)
    for dirname in ('crosscti','scripts'):
        if (workspace/dirname).exists():raise RuntimeError('WORKSPACE_ALREADY_EXISTS '+str(workspace))
        shutil.copytree(src/dirname,workspace/dirname)
    (workspace/'config').mkdir(exist_ok=True)
    cfg=load(src/'config/study.json')
    cfg['protocol']=REPAIR_PROTOCOL
    cfg['source_dataset']='CZLi/apt-reports publisher APT subset; archived originals'
    cfg['dataset_url']='https://huggingface.co/datasets/CZLi/apt-reports'
    cfg['source_names']=chosen
    cfg['min_publishers']=len(chosen)
    cfg['exact_sign_test']='publisher-level 2^9 exhaustive sign flips; two-sided'
    cfg['source_release_revision']=p['revision']
    cfg['source_release_index_sha256']=p['files']['filename_map.json']['sha256']
    cfg['source_provenance_status']='COLLECTOR_INDEX_ARCHIVE_MATCHED_CPU_ONLY'
    save(workspace/'config/study.json',cfg)
    (workspace/'dataset').mkdir(exist_ok=True)
    save(workspace/'dataset/reports.json',[
      {'source':r['source'],'text':r['text'],'url':r['url'],
       'archive_path':r['zip_path'],'html_sha256':r['html_sha256']} for r in selected])
    h=hashlib.sha256()
    with archive.open('rb') as file:
        for chunk in iter(lambda:file.read(8*1024*1024),b''):
            h.update(chunk)
    stages={'status':'CPU_CORPUS_STAGED_PENDING_TOKENIZER_AND_OVERLAP_GATES',
            'repo_id':REPO_ID,'revision':p['revision'],
            'archive_sha256':h.hexdigest(),
            'index_sha256':p['files']['filename_map.json']['sha256'],
            'sources':chosen,'eligible_counts':full_counts,'selected':72,
            'selection_salt':SALT,'discard_counts':dict(count),
            'smah_inputs_sha256':sha(smah_inputs.read_bytes()) if smah_inputs else None,
            'smah_baseline_unique_sentences':len(baseline),
            'excluded_for_overlap':excluded,
            'overlap_repair_status':'FULL_REPORT_SENTENCE_EXCLUSION_PASS',
            'records':[{'source':r['source'],'number':r['number'],'url':r['url'],
                        'archive_path':r['zip_path'],'html_sha256':r['html_sha256'],
                        'text_sha256':r['text_sha256']} for r in selected],
            'no_gpu_runs':True}
    save(workspace/'dataset/corpus_provenance.json',stages)
    m=prepare(workspace/'dataset/reports.json',workspace)
    # The runner deliberately remains closed in this CPU-staging release.
    assert m['windows']==144 and m['total_calls']==6912
    return {'status':'CPU_CORPUS_STAGED','workspace':str(workspace),
            'selected_sources':chosen,'selected_reports':len(selected),
            'input_windows':m['windows'],'planned_gpu_calls':m['total_calls'],
            'dataset_sha256':m['dataset_sha256'],'data_gate':'PASS',
            'tokenizer_gate':'NOT_RUN','gpu_gate':'CLOSED',
            'excluded_for_overlap':len(excluded),'smah_baseline_unique_sentences':len(baseline)}


def download_archive(meta, destination, *, confirm_large=False):
    if not confirm_large:
        raise RuntimeError('LARGE_ARCHIVE_DOWNLOAD_REQUIRES_--confirm-large (10.7 GB)')
    from huggingface_hub import hf_hub_download
    p=checked_index(Path(meta))
    remote=Path(hf_hub_download(REPO_ID,filename=ARCHIVE,repo_type='dataset',revision=p['revision']))
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists():
        # Hardlink avoids a redundant 10.7 GB copy if cache/destination share a disk.
        try:destination.hardlink_to(remote)
        except OSError:shutil.copy2(remote,destination)
    return {'archive':str(destination),'size_bytes':destination.stat().st_size,
            'zip_ok':zipfile.is_zipfile(destination)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('metadata');a.add_argument('--dest',required=True);a.add_argument('--revision')
    a=sub.add_parser('inspect');a.add_argument('--meta',required=True)
    a=sub.add_parser('download');a.add_argument('--meta',required=True);a.add_argument('--dest',required=True);a.add_argument('--confirm-large',action='store_true')
    a=sub.add_parser('stage');a.add_argument('--meta',required=True);a.add_argument('--archive',required=True);a.add_argument('--workspace',required=True);a.add_argument('--base-study',default='.');a.add_argument('--smah-inputs',required=True)
    a=p.parse_args()
    if a.command=='metadata':out=fetch_indexes(Path(a.dest),a.revision)
    elif a.command=='inspect':out=summarize_index(Path(a.meta))
    elif a.command=='download':out=download_archive(a.meta,a.dest,confirm_large=a.confirm_large)
    else:out=stage_archive(a.meta,a.archive,a.workspace,a.base_study,a.smah_inputs)
    print(json.dumps(out,sort_keys=True,indent=2))

if __name__=='__main__':main()
