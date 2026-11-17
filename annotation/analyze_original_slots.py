#!/usr/bin/env python3
"""Decision quality on the ORIGINAL annotation slots of the human-labelled draw.

The main human-label analysis (build_human_slot_labels.py) attaches each sentence
label to every slot carrying that sentence, which yields 371 labelled slots in 55
windows. This script instead restricts the analysis to the 288 slots the experts
were actually shown: the 36 windows (9 publishers x 4 reports x 1 window, all
eight targets) of the kit's draw. No label is copied to any other slot.

Recovering the draw without the private identifier map
------------------------------------------------------
32 of the 36 windows are uniquely identified (in_identified_window = 1). The other
four come from two classes of text-identical windows in different reports of the
source collection: one securelist window (2 copies) and one groupib window (8 copies).
The draw contains 1 window of the securelist class and 3 of the groupib class.
`--a1` (author only) re-derives this from the item texts: it enumerates every
36-window set, drawn from the fully labelled windows, whose 288 sentence hashes equal
the multiset of the 288 item hashes, and confirms that all such sets differ only by
swapping text-identical windows. Because the copies also received identical model
decisions in every arm, model, precision and example index (checked below from the
released decisions), every quantity computed here is the same whichever copies are
taken; the windows listed in draw_windows.csv are one such choice.

Variants (each run for every label set)
  draw288   the 288 original slots, as drawn (the groupib window counts three times)
  distinct  content-distinct windows only (the three identical groupib windows count
            once): 34 windows, 272 slots
Label sets: adjudicated (primary), h_agree (labels H1 and H2 agreed on before
adjudication), a1, a2, label (three-rater majority), ai (the AI annotator on the same slots).

External check: the E1 protocol's human-reference F1 guardrail was computed author-side
with the private identifier map. Recomputed on the reconstructed draw from the released
E1 decisions, all confusion counts and the publisher-level F1 difference-in-differences
must match the author-side values exactly; the script stops otherwise.

Outputs: results/human_labels_original/<variant>/<label set>/ (same files as
analyze_ai_labels.py), results/human_labels_original/effective_sample_size.json and
results/human_labels_original/e1_guardrail.json.
Standard library only, apart from the optional --a1 check.
"""
import argparse, collections, csv, hashlib, itertools, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from analyze_annotation import load_decisions, MODELS, PRECISIONS, ARMS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--slots', type=Path, default=HERE / 'human_labels' / 'human_labels_by_slot.csv')
ap.add_argument('--draw', type=Path, default=HERE / 'human_labels' / 'draw_windows.csv')
ap.add_argument('--a1', type=Path, help='author only: private item sheet, to re-derive the draw from item texts')
ap.add_argument('--out', type=Path, default=ROOT / 'results' / 'human_labels_original')
ap.add_argument('--a-zip', type=Path, default=ROOT / 'checkpoints' / 'v216_armA_results_redacted.zip')
ap.add_argument('--bc-zip', type=Path, default=ROOT / 'checkpoints' / 'v221_armBC_and_replay_results.zip')
a = ap.parse_args()

rows = list(csv.DictReader(a.slots.open(encoding='utf-8')))
byw = collections.defaultdict(dict)
for r in rows: byw[r['window_id']][int(r['target_index'])] = r
labelled = lambda r: any(r[c] != '' for c in ('a1', 'a2', 'ai', 'adjudicated'))
seq = lambda w: tuple(byw[w][t]['text_sha256'] for t in range(8))
full = sorted(w for w, s in byw.items() if all(labelled(s[t]) for t in range(8)))
sure = sorted(w for w in full if byw[w][0]['in_identified_window'] == '1')
draw = [r for r in csv.DictReader(a.draw.open())]
D = [r['window_id'] for r in draw]
assert len(D) == 36 and len(set(D)) == 36 and set(sure) <= set(D) and set(D) <= set(full)
pub = lambda w: byw[w][0]['publisher']; rep = lambda w: byw[w][0]['report_id']
assert set(collections.Counter(pub(w) for w in D).values()) == {4}
assert len({rep(w) for w in D}) == 36

# text-identical classes among fully labelled windows
cls = collections.defaultdict(list)
for w in full: cls[seq(w)].append(w)
check = {'fully_labelled_windows': len(full), 'uniquely_identified': len(sure),
         'duplicate_classes': [{'publisher': pub(ws[0]), 'copies': len(ws), 'in_draw': sum(w in D for w in ws)}
                               for ws in cls.values() if len(ws) > 1]}

# decisions must be identical across text-identical copies
dupw = {w for ws in cls.values() if len(ws) > 1 for w in ws}
dec = load_decisions(set(D) | dupw, a.a_zip, a.bc_zip)
cells = diff = 0
for ws in cls.values():
    if len(ws) < 2: continue
    for arm, m, p, k in itertools.product(ARMS, MODELS, PRECISIONS, range(8)):
        cells += 1; diff += len({frozenset(dec[(arm, m, p, w, k)]) for w in ws}) > 1
assert diff == 0, 'copies differ in model decisions; the draw is not determined'
check['decision_cells_compared_across_copies'] = cells
check['decision_cells_differing'] = diff

if a.a1:  # author-only re-derivation from the item texts
    A1 = list(csv.DictReader(a.a1.open(encoding='utf-8-sig')))
    item = collections.Counter(hashlib.sha256(r['target_sentence'].encode('utf-8')).hexdigest() for r in A1)
    assert sum(item.values()) == 288
    base = collections.Counter(h for w in sure for h in seq(w))
    rest = [w for w in full if w not in sure]
    sols = [c for c in itertools.combinations(rest, 36 - len(sure))
            if collections.Counter(h for w in c for h in seq(w)) == item - base
            and set(collections.Counter(pub(w) for w in list(sure) + list(c)).values()) == {4}
            and len({rep(w) for w in list(sure) + list(c)}) == 36]
    canon = {tuple(sorted(seq(w) for w in c)) for c in sols}
    assert len(canon) == 1 and tuple(sorted(seq(w) for w in D if w not in sure)) in canon
    check['a1_rederivation'] = {'consistent_window_sets': len(sols), 'distinct_by_content': len(canon),
                                'listed_draw_is_one_of_them': True}
else:  # public rerun: keep the author-side record of the re-derivation so the outputs stay byte-identical
    prev = a.out / 'effective_sample_size.json'
    if prev.is_file():
        rec = json.loads(prev.read_text()).get('check', {}).get('a1_rederivation')
        if rec: check['a1_rederivation'] = rec

# content-distinct variant: one copy per text-identical class within the draw
seen, distinct = set(), []
for w in D:
    if seq(w) in seen: continue
    seen.add(seq(w)); distinct.append(w)

COLS = ('adjudicated', 'h_agree', 'a1', 'a2', 'label', 'ai')
FIELDS = list(rows[0].keys())


def write_subset(path, wins):
    keep = set(wins)
    with path.open('w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS); wr.writeheader()
        for r in rows:
            if r['window_id'] in keep: wr.writerow(r)
            else: wr.writerow({**r, **{c: '' for c in COLS}})


def ess(wins, col):
    """slots, distinct sentences and Kish effective n of the labelled slots of `wins`."""
    s = [byw[w][t] for w in wins for t in range(8) if byw[w][t][col] in ('0', '1')]
    c = collections.Counter(r['text_sha256'] for r in s)
    return {'labelled_slots': len(s), 'distinct_sentences': len(c),
            'kish_effective_n': round(sum(c.values()) ** 2 / sum(v * v for v in c.values()), 1),
            'relevant': sum(r[col] == '1' for r in s), 'windows': len(set(r['window_id'] for r in s)),
            'reports': len({r['report_id'] for r in s}), 'publishers': len({r['publisher'] for r in s})}


# ---- external check: the E1 protocol's human-reference F1 guardrail was computed author-side with the
# private identifier map (extensions/E5_synthesis/evidence/E1_cell_quality.csv, E1_F1_interaction_DID.csv).
# Recomputing it on the reconstructed draw from the released E1 decisions must give the same counts.
EV = ROOT / 'extensions' / 'E5_synthesis' / 'evidence'
glab = {(w, t): int(byw[w][t]['adjudicated']) for w in D for t in range(8) if byw[w][t]['adjudicated'] in ('0', '1')}
E1 = {(r['model'], r['precision'], r['condition'], r['window_id']):
      (set(json.loads(r['indices_json'])) if r['valid'] == '1' else set())
      for r in csv.DictReader((EV / 'E1_window_decisions_1728.csv').open())}


def e1_counts(m, p, c, wins):
    tp = fp = fn = tn = 0
    for w in wins:
        S = E1[(m, p, c, w)]
        for t in range(8):
            y = glab.get((w, t))
            if y is None: continue
            s = t in S; tp += s and y == 1; fp += s and y == 0; fn += (not s) and y == 1; tn += (not s) and y == 0
    return tp, fp, fn, tn


def sign_p(xs):
    obs = abs(sum(xs))
    return sum(abs(sum(x * g for x, g in zip(xs, sg))) >= obs - 1e-12
               for sg in itertools.product((-1, 1), repeat=len(xs))) / 2 ** len(xs)


f1_ = lambda c: 2 * c[0] / (2 * c[0] + c[1] + c[2])
e1 = {'cells': [], 'did': []}
for r in csv.DictReader((EV / 'E1_cell_quality.csv').open()):
    c = e1_counts(r['model'], r['precision'], r['condition'], D)
    same = c == tuple(int(r[k]) for k in ('TP', 'FP', 'FN', 'TN'))
    e1['cells'].append({'model': r['model'], 'precision': r['precision'], 'condition': r['condition'],
                        'TP': c[0], 'FP': c[1], 'FN': c[2], 'TN': c[3], 'F1': f1_(c), 'matches_author_side': same})
pubs9 = sorted({pub(w) for w in D})
for r in csv.DictReader((EV / 'E1_F1_interaction_DID.csv').open()):
    m = r['model']; dd = []
    for g in pubs9:
        ws = [w for w in D if pub(w) == g]
        F = {(p_, c_): f1_(e1_counts(m, p_, c_, ws)) for p_ in ('bf16', 'nf4') for c_ in ('N0', 'N1')}
        dd.append((F[('nf4', 'N1')] - F[('bf16', 'N1')]) - (F[('nf4', 'N0')] - F[('bf16', 'N0')]))
    est, pv = 100 * sum(dd) / len(dd), sign_p(dd)
    e1['did'].append({'model': m, 'did_pp': est, 'p_exact_signflip': pv, 'positive': sum(x > 0 for x in dd), 'negative': sum(x < 0 for x in dd),
                      'matches_author_side': abs(est - float(r['publisher_equal_DID_pp'])) < 1e-9 and abs(pv - float(r['exact_signflip_p'])) < 1e-12})
assert all(x['matches_author_side'] for x in e1['cells'] + e1['did']), 'reconstructed draw does not reproduce the author-side E1 guardrail'
check['e1_guardrail_reproduced'] = {'cells': len(e1['cells']), 'did': len(e1['did']), 'all_match': True}

# ---- the released agreement statistics were computed on the 288 items; on the recovered draw the
# slot labels are the item labels, so Cohen's kappa must reproduce exactly from the public slot file
AGR = json.loads((HERE / 'human_labels' / 'agreement.json').read_text())
dslots = [byw[w][t] for w in D for t in range(8)]
for x, y in itertools.combinations(('a1', 'a2', 'ai'), 2):
    pr = [(int(u[x]), int(u[y])) for u in dslots if u[x] in ('0', '1') and u[y] in ('0', '1')]
    n = len(pr); po = sum(u == v for u, v in pr) / n
    pa = sum(u for u, _ in pr) / n; pb = sum(v for _, v in pr) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    ref = AGR['pairwise'][f'{x}-{y}']
    assert n == ref['n'] and abs((po - pe) / (1 - pe) - ref['cohen_kappa']) < 1e-12, f'agreement {x}-{y} does not reproduce'
check['agreement_reproduced_from_slots'] = True

expanded = sorted({r['window_id'] for r in rows if r['adjudicated'] != '' or r['a1'] != ''})
summary = {'check': check, 'draw_windows': len(D), 'distinct_windows': len(distinct),
           'effective_sample_size': {v: {c: ess(ws, c) for c in COLS}
                                     for v, ws in (('expanded371', expanded), ('draw288', D), ('distinct', distinct))}}
a.out.mkdir(parents=True, exist_ok=True)
for variant, wins in (('draw288', D), ('distinct', distinct)):
    sub = a.out / variant; sub.mkdir(exist_ok=True)
    lab = sub / 'labels_by_slot.csv'; write_subset(lab, wins)
    for c in COLS:
        subprocess.run([sys.executable, str(HERE / 'analyze_ai_labels.py'), '--labels', str(lab), '--label-column', c,
                        '--partial', '--a-zip', str(a.a_zip), '--bc-zip', str(a.bc_zip), '--out', str(sub / c)],
                       check=True, stdout=subprocess.DEVNULL)
json.dump(summary, (a.out / 'effective_sample_size.json').open('w'), indent=1)
json.dump(e1, (a.out / 'e1_guardrail.json').open('w'), indent=1)
print(json.dumps(summary['effective_sample_size'], indent=1))
print('ORIGINAL_SLOT_ANALYSIS_DONE', a.out)
