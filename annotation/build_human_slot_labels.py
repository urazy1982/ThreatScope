#!/usr/bin/env python3
"""Author-only step: combine the three annotations of the 288-item labelled subset.

Annotators: a1 and a2 (human cybersecurity professionals) and ai (claude-fable-5-2,
whose labels for the same items come from its 1,152-item pass). All three files use
the labelling kit's schema (item_id, target_sentence, label in {1,0,U}, category,
confidence, evidence_note).

Gold label (pre-declared here, before any decision-quality result was computed):
  majority of the three annotators over {0,1}; U counts as an abstention;
  if fewer than two annotators agree on 0 or on 1 the item has no gold label.
Adjudicated expert label (column adjudicated, primary once available): the H1-H2
agreed label, or for disagreements the label H1 and H2 agreed in joint adjudication
(make_adjudication_sheet.py); U or blank -> no label.
Human-only alternative (column h_agree): the label on which a1 and a2 agree; items
on which they disagree, or that either marked U, have no h_agree label.

Items are linked to study slots by exact sentence text. Within every annotator,
identical sentences carry identical labels (checked below), so a text-level label
is well defined. Every slot whose sentence was labelled receives that label; the
slot file records whether the slot lies in one of the 32 windows that are uniquely
identified as belonging to the kit's 36-window subset.

Outputs (text-free, distributable):
  annotation/human_labels/human_labels_by_slot.csv
  annotation/human_labels/agreement.json
"""
import argparse, collections, csv, hashlib, json, itertools
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--inputs', required=True, type=Path)
ap.add_argument('--a1', required=True, type=Path)
ap.add_argument('--a2', required=True, type=Path)
ap.add_argument('--ai', required=True, type=Path, help='AI package CSV with sentences (1,152 items)')
ap.add_argument('--out', type=Path, default=Path(__file__).resolve().parent / 'human_labels')
ap.add_argument('--adjudication', type=Path, help='completed joint-adjudication workbook or CSV (item_id, agreed_label)')
a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)

rd = lambda p: list(csv.DictReader(p.open(encoding='utf-8-sig')))
A1, A2, AIall = rd(a.a1), rd(a.a2), {r['item_id']: r for r in rd(a.ai)}
assert [r['item_id'] for r in A1] == [r['item_id'] for r in A2] and len(A1) == 288
for r1, r2 in zip(A1, A2):
    ws = lambda t: ' '.join(t.replace('\\r\\n', ' ').replace('\\n', ' ').split())  # a2's export turned one item's literal \\r\\n escapes into line breaks
    assert r1['target_sentence'] == AIall[r1['item_id']]['target_sentence'] and ws(r1['target_sentence']) == ws(r2['target_sentence'])
ANN = {'a1': {r['item_id']: r for r in A1}, 'a2': {r['item_id']: r for r in A2},
       'ai': {r['item_id']: AIall[r['item_id']] for r in A1}}
ids = [r['item_id'] for r in A1]
adj = {}
if a.adjudication:
    if a.adjudication.suffix.lower() == '.xlsx':
        import openpyxl
        ws = openpyxl.load_workbook(a.adjudication, read_only=True, data_only=True)['adjudicate']
        it = ws.iter_rows(values_only=True); hdr = [str(h) for h in next(it)]
        arows = [dict(zip(hdr, r)) for r in it]
    else:
        arows = list(csv.DictReader(a.adjudication.open(encoding='utf-8-sig')))
    for r in arows:
        if not r.get('item_id'): continue
        v = str(r.get('agreed_label') if r.get('agreed_label') is not None else '').strip().upper()
        if v.endswith('.0'): v = v[:-2]
        if v not in ('0', '1', 'U', ''): raise SystemExit(f"bad agreed_label {v!r} for {r['item_id']}")
        adj[str(r['item_id'])] = v
text = {i: ANN['a1'][i]['target_sentence'] for i in ids}

# text-level labels, with a consistency check
tl = {}
for n, X in ANN.items():
    g = collections.defaultdict(set)
    for i in ids: g[text[i]].add(X[i]['label'])
    if any(len(v) > 1 for v in g.values()): raise SystemExit(f'INCONSISTENT_LABELS_FOR_IDENTICAL_TEXT {n}')
    tl[n] = {t: next(iter(v)) for t, v in g.items()}


def majority(labs):
    c = collections.Counter(l for l in labs if l in ('0', '1'))
    for k in ('0', '1'):
        if c[k] >= 2: return k
    return ''


# ---- agreement statistics on the 288 items
def kappa(x, y):
    p = [(int(u), int(v)) for u, v in zip(x, y) if u in '01' and v in '01' and u and v]
    n = len(p); po = sum(u == v for u, v in p) / n
    pa = sum(u for u, _ in p) / n; pb = sum(v for _, v in p) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    return {'n': n, 'raw_agreement': po, 'cohen_kappa': (po - pe) / (1 - pe)}


lab = {n: [ANN[n][i]['label'] for i in ids] for n in ANN}
pair = {f'{x}-{y}': kappa(lab[x], lab[y]) for x, y in itertools.combinations(ANN, 2)}
full = [i for i in ids if all(ANN[n][i]['label'] in ('0', '1') for n in ANN)]
N = len(full); k = 3
P_i = []; tot1 = 0
for i in full:
    n1 = sum(ANN[n][i]['label'] == '1' for n in ANN); tot1 += n1
    P_i.append((n1 * (n1 - 1) + (k - n1) * (k - n1 - 1)) / (k * (k - 1)))
p1 = tot1 / (N * k); Pbar = sum(P_i) / N; Pe = p1 ** 2 + (1 - p1) ** 2
fleiss = (Pbar - Pe) / (1 - Pe)
def adjudicated(i):
    l1, l2 = ANN['a1'][i]['label'], ANN['a2'][i]['label']
    if l1 == l2 and l1 in ('0', '1'): return l1
    v = adj.get(i, '')
    return v if v in ('0', '1') else ''
need_adj = [i for i in ids if not (ANN['a1'][i]['label'] == ANN['a2'][i]['label'] and ANN['a1'][i]['label'] in ('0', '1'))]
adj_lab = {i: adjudicated(i) for i in ids}
tl['adjudicated'] = {}
for i in ids:
    t = text[i]
    if t in tl['adjudicated'] and tl['adjudicated'][t] != adj_lab[i]:
        raise SystemExit('INCONSISTENT_ADJUDICATION_FOR_IDENTICAL_TEXT')
    tl['adjudicated'][t] = adj_lab[i]
hum = kappa(lab['a1'], lab['a2'])
import random
rng = random.Random(20261113); bo = {k: [] for k in pair}
for _ in range(2000):
    smp = [rng.randrange(len(ids)) for _ in ids]
    for x, y in itertools.combinations(ANN, 2):
        try: bo[f'{x}-{y}'].append(kappa([lab[x][j] for j in smp], [lab[y][j] for j in smp])['cohen_kappa'])
        except ZeroDivisionError: pass
for k, v in bo.items():
    v.sort(); pair[k]['ci95_item_bootstrap'] = [v[int(.025 * len(v))], v[int(.975 * len(v)) - 1]]
odd = {f'{n}_only_relevant': sum(ANN[n][i]['label'] == '1' and all(ANN[m][i]['label'] == '0' for m in ANN if m != n) for i in ids) for n in ANN}
odd.update({f'{n}_only_irrelevant': sum(ANN[n][i]['label'] == '0' and all(ANN[m][i]['label'] == '1' for m in ANN if m != n) for i in ids) for n in ANN})
gold = {i: majority([ANN[n][i]['label'] for n in ANN]) for i in ids}
summary = {
    'items': len(ids), 'distinct_texts': len(set(text.values())),
    'label_counts': {n: dict(collections.Counter(lab[n])) for n in ANN},
    'pairwise': pair, 'fleiss_kappa_three': {'items_all_three_binary': N, 'kappa': fleiss},
    'all_three_agree': sum(len({ANN[n][i]['label'] for n in ANN}) == 1 and ANN['a1'][i]['label'] in '01' for i in ids),
    'gold_rule': 'majority of a1, a2, ai over {0,1}; U abstains; no gold if no label has two votes',
    'gold_counts': dict(collections.Counter(gold.values())),
    'adjudication': {'items_needing_adjudication': len(need_adj),
                     'items_adjudicated': sum(adj.get(i, '') in ('0', '1', 'U') for i in need_adj),
                     'complete': all(adj.get(i, '') in ('0', '1', 'U') for i in need_adj),
                     'adjudicated_counts': dict(collections.Counter(adj_lab.values())),
                     'agreement_with': {n: kappa([adj_lab[i] or 'x' for i in ids], lab[n]) if adj else None for n in ANN},
                     'resolved_to_h1': sum(adj.get(i) == ANN['a1'][i]['label'] for i in need_adj),
                     'resolved_to_h2': sum(adj.get(i) == ANN['a2'][i]['label'] for i in need_adj),
                     'resolved_to_neither': sum(adj.get(i) not in (ANN['a1'][i]['label'], ANN['a2'][i]['label']) for i in need_adj),
                     'agreed_label_counts': dict(collections.Counter(adj.get(i, '') for i in need_adj)),
                     'binary_disagreements': sum(ANN['a1'][i]['label'] in ('0', '1') and ANN['a2'][i]['label'] in ('0', '1') for i in need_adj),
                     'binary_resolved_to_h1': sum(ANN['a1'][i]['label'] in ('0', '1') and ANN['a2'][i]['label'] in ('0', '1') and adj.get(i) == ANN['a1'][i]['label'] for i in need_adj)},
    'outvoted': odd, 'h_agree_counts': dict(collections.Counter(lab['a1'][j] if lab['a1'][j] == lab['a2'][j] and lab['a1'][j] in '01' else '' for j in range(len(ids)))),
    'confidence_counts': {n: dict(collections.Counter(ANN[n][i]['confidence'] for i in ids)) for n in ANN},
    'notes_per_category_a2': {c: len({ANN['a2'][i]['evidence_note'] for i in ids if ANN['a2'][i]['category'] == c}) for c in {ANN['a2'][i]['category'] for i in ids}},
    'qc': {n: {'distinct_evidence_notes': len({ANN[n][i]['evidence_note'] for i in ids}),
               'confidence_determined_by_category': all(
                   len({ANN[n][i]['confidence'] for i in ids if ANN[n][i]['category'] == c}) == 1
                   for c in {ANN[n][i]['category'] for i in ids})} for n in ANN},
}

# ---- slots
windows = [json.loads(l) for l in a.inputs.open(encoding='utf-8') if l.strip()]
need = collections.Counter(text[i] for i in ids)
allc = collections.Counter(s['sentence_text'] for w in windows for s in w['sentences'])
sure = {w['window_id'] for w in windows
        if all(s['sentence_text'] in need for s in w['sentences'])
        and any(allc[s['sentence_text']] == 1 for s in w['sentences'])}
summary['windows_uniquely_identified'] = len(sure)
with (a.out / 'human_labels_by_slot.csv').open('w', newline='', encoding='utf-8') as f:
    wr = csv.writer(f)
    wr.writerow(['window_id', 'report_id', 'publisher', 'target_index', 'a1', 'a2', 'ai', 'label', 'h_agree', 'adjudicated',
                 'confidence', 'in_identified_window', 'text_sha256'])
    nl = 0
    for w in windows:
        for i, s in enumerate(w['sentences']):
            t = s['sentence_text']
            if t in tl['a1']:
                L = [tl[n][t] for n in ('a1', 'a2', 'ai')]; g = majority(L); nl += 1
                ha = L[0] if L[0] == L[1] and L[0] in ('0', '1') else ''
                ad = tl['adjudicated'][t]
            else:
                L = ['', '', '']; g = ''; ha = ''; ad = ''
            wr.writerow([w['window_id'], w['report_id'], w['source'], i, *L, g, ha, ad, 'high',
                         int(w['window_id'] in sure), hashlib.sha256(t.encode()).hexdigest()])
summary['labelled_slots'] = nl
json.dump(summary, (a.out / 'agreement.json').open('w'), indent=1)
print(json.dumps({k: summary[k] for k in ('pairwise', 'fleiss_kappa_three', 'gold_counts', 'labelled_slots', 'windows_uniquely_identified')}, indent=1))
