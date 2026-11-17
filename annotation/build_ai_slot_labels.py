#!/usr/bin/env python3
"""Author-only step: attach AI-generated relevance labels to study slots.

The AI annotation package labels 1,152 blinded items (item_id + sentence). The
blinding key is not part of the package, so items are matched to study slots
(window_id, target index) by exact sentence text. Identical sentences received
identical labels (the package's validation reports zero conflicts), and the
multiset of sentences in the package equals the multiset of target slots, so the
match is lossless for labels. This is checked below and the script stops if not.

Input : the original prepared inputs.jsonl (contains report text; not distributed)
        the AI package CSV with sentences (keep private)
Output: annotation/ai_labels/ai_labels_by_slot.csv  -- text-free, distributable
"""
import argparse, collections, csv, hashlib, json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--inputs', required=True, type=Path)
ap.add_argument('--ai-csv', required=True, type=Path)
ap.add_argument('--revisions', type=Path)
ap.add_argument('--out', type=Path, default=Path(__file__).resolve().parent / 'ai_labels' / 'ai_labels_by_slot.csv')
a = ap.parse_args()

ai = list(csv.DictReader(a.ai_csv.open(encoding='utf-8-sig')))
windows = [json.loads(l) for l in a.inputs.open(encoding='utf-8') if l.strip()]
slots = [(w['window_id'], w['report_id'], w['source'], i, s['sentence_text'])
         for w in windows for i, s in enumerate(w['sentences'])]
assert len(ai) == len(slots) == 1152, (len(ai), len(slots))
by_text = collections.defaultdict(list)
for r in ai:
    by_text[r['target_sentence']].append(r)
if collections.Counter(r['target_sentence'] for r in ai) != collections.Counter(t for *_, t in slots):
    raise SystemExit('TEXT_MULTISET_MISMATCH: cannot map AI items to slots')
for t, rs in by_text.items():
    if len({(r['label'], r['category'], r['confidence']) for r in rs}) != 1:
        raise SystemExit('CONFLICTING_LABELS_FOR_IDENTICAL_TEXT')
revised = set()
if a.revisions and a.revisions.exists():
    revised = {r['item_id'] for r in csv.DictReader(a.revisions.open(encoding='utf-8-sig'))}
a.out.parent.mkdir(parents=True, exist_ok=True)
with a.out.open('w', newline='', encoding='utf-8') as f:
    wr = csv.writer(f)
    wr.writerow(['window_id', 'report_id', 'publisher', 'target_index', 'label', 'category', 'confidence',
                 'item_ids', 'revised_before_export', 'text_sha256'])
    for wid, rid, src, i, t in slots:
        rs = by_text[t]; r = rs[0]
        ids = sorted(x['item_id'] for x in rs)
        wr.writerow([wid, rid, src, i, r['label'], r['category'], r['confidence'], ';'.join(ids),
                     int(any(x in revised for x in ids)), hashlib.sha256(t.encode('utf-8')).hexdigest()])
print('AI_SLOT_LABELS_WRITTEN', a.out, len(slots))
