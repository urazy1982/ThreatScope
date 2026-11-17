"""Optional CPU collision audit against SMAH-CTI original sentence data."""
from __future__ import annotations
import argparse,collections,json,re
from .core import read,lines,digest

def normal(s):return ' '.join(s.casefold().split())
def check(root,smah):
    rows=read(smah)
    if not isinstance(rows,list):raise ValueError('EXPECTED_ORIGINAL_SMAH_LIST')
    old={digest(normal(r['sentence_text'])) for r in rows if isinstance(r,dict) and isinstance(r.get('sentence_text'),str)}
    windows=lines(str(root)+'/outputs/prepared/inputs.jsonl')
    matches=collections.defaultdict(list)
    for w in windows:
      for s in w['sentences']:
        if digest(normal(s['sentence_text'])) in old:matches[w['source']].append(s['uid'])
    report={'smah_sentence_count':len(old),'prepared_sentences':8*len(windows),
            'exact_normalized_overlap_count':sum(len(x) for x in matches.values()),
            'matches_by_source':{k:len(v) for k,v in matches.items()}}
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--smah',required=True)
    a=p.parse_args();print(json.dumps(check(a.root,a.smah),indent=2))
if __name__=='__main__':main()
