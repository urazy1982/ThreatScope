#!/usr/bin/env python3
"""Exploratory analysis of model decisions against AI-GENERATED reference labels.

The labels (annotation/ai_labels/ai_labels_by_slot.csv) were produced by one LLM
(claude-fable-5-2) in a single pass. They are NOT human judgments and NOT ground
truth. This analysis was added after all model results were known; it is not part
of any pre-specified protocol. Standard library only.

Outputs (results/ai_labels/):
  quality.csv        P/R/F1 (Arms A, B) or top-1 relevance (Arm C) per arm x model x precision,
                     pooled, with hierarchical publisher->report bootstrap CIs, and the
                     NF4-BF16 difference with exact publisher sign-flip p
  stratified.csv     NF4-BF16 example-index interaction on AI-relevant / AI-irrelevant targets
  flips.csv          BF16->NF4 decision changes by AI label and on-/off-example position
  sensitivity.csv    key quantities under alternative label handling and on the human subset
  summary.json       everything above plus label counts and settings
"""
import argparse, csv, itertools, json, random, sys, zipfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from analyze_annotation import load_decisions, MODELS, PRECISIONS, ARMS  # noqa: E402

BOOT = 2000; SEED = 20261113

ap = argparse.ArgumentParser()
ap.add_argument('--labels', type=Path, default=HERE / 'ai_labels' / 'ai_labels_by_slot.csv')
ap.add_argument('--a-zip', type=Path, default=ROOT / 'checkpoints' / 'v216_armA_results_redacted.zip')
ap.add_argument('--bc-zip', type=Path, default=ROOT / 'checkpoints' / 'v221_armBC_and_replay_results.zip')
ap.add_argument('--subset', type=Path, default=HERE / 'subset_windows.csv')
ap.add_argument('--out', type=Path, default=ROOT / 'results' / 'ai_labels')
ap.add_argument('--label-column', default='label', help='column holding 1/0/U (blank = not labelled)')
ap.add_argument('--partial', action='store_true', help='labels cover only some slots; skip the 1,152-slot sensitivity block')
a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)

rows = list(csv.DictReader(a.labels.open(encoding='utf-8')))
assert len(rows) == 1152 or a.partial
for r in rows:
    r['label'] = r[a.label_column]
    r.setdefault('confidence', 'high')
rows = [r for r in rows if r['label'] in ('0', '1', 'U')]
lab = {(r['window_id'], int(r['target_index'])): r for r in rows}
win = {}
for r in rows:
    win[r['window_id']] = (r['publisher'], r['report_id'])
pubs = sorted({p for p, _ in win.values()}); assert len(pubs) == 9
dec = load_decisions(set(win), a.a_zip, a.bc_zip)
subset = {r['window_id'] for r in csv.DictReader(a.subset.open())}


def gold_map(mode):
    """mode: primary (U excluded) | U0 | U1 | conf (low-confidence and U excluded)"""
    g = {}
    for k, r in lab.items():
        L = r['label']
        if L == 'U':
            if mode == 'U0': g[k] = 0
            elif mode == 'U1': g[k] = 1
            continue
        if mode == 'conf' and r['confidence'] == 'low':
            continue
        g[k] = int(L)
    return g


def sign_p(xs):
    xs = list(xs); obs = abs(sum(xs))
    return sum(abs(sum(x * s for x, s in zip(xs, sg))) >= obs - 1e-12
               for sg in itertools.product((-1, 1), repeat=len(xs))) / 2 ** len(xs)


def cells(arm, m, p, wins, g):
    """per-window list of (tp, fp, fn, sel, chosen_relevant_for_C, chosen_labelled_for_C)"""
    out = {}
    for w in wins:
        tp = fp = fn = sel = cr = cl = 0
        for k in range(8):
            S = dec[(arm, m, p, w, k)]
            for t in range(8):
                y = g.get((w, t))
                if y is None: continue
                s = t in S
                tp += s and y == 1; fp += s and y == 0; fn += (not s) and y == 1; sel += s
                if s: cl += 1; cr += y
        out[w] = (tp, fp, fn, sel, cr, cl)
    return out


def metric(arm, agg):
    tp, fp, fn, sel, cr, cl = agg
    if arm == 'C':
        return cr / cl if cl else float('nan')
    pr = tp / (tp + fp) if tp + fp else float('nan'); rc = tp / (tp + fn) if tp + fn else float('nan')
    return 2 * pr * rc / (pr + rc) if pr == pr and rc == rc and pr + rc else float('nan')


def add(ws, c):
    s = [0] * 6
    for w in ws:
        for i, v in enumerate(c[w]): s[i] += v
    return s


def structure(wins):
    st = defaultdict(lambda: defaultdict(list))
    for w in wins:
        p, r = win[w]; st[p][r].append(w)
    return st


def boot_ci(st, f, rng):
    ps = sorted(st); vals = []
    for _ in range(BOOT):
        ws = []
        for p in (rng.choice(ps) for _ in ps):
            rs = sorted(st[p])
            for r in (rng.choice(rs) for _ in rs): ws.extend(st[p][r])
        v = f(ws)
        if v == v: vals.append(v)
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))]


def quality(g, wins, rng, tag):
    st = structure(wins); res = []
    for arm in ARMS:
        for m in MODELS:
            c = {p: cells(arm, m, p, wins, g) for p in PRECISIONS}
            agg = {p: add(wins, c[p]) for p in PRECISIONS}
            val = {p: metric(arm, agg[p]) for p in PRECISIONS}
            ci = {p: boot_ci(st, lambda ws, p=p: metric(arm, add(ws, c[p])), rng) for p in PRECISIONS}
            dci = boot_ci(st, lambda ws: metric(arm, add(ws, c['nf4'])) - metric(arm, add(ws, c['bf16'])), rng)
            pubd = [metric(arm, add([w for w in wins if win[w][0] == q], c['nf4'])) -
                    metric(arm, add([w for w in wins if win[w][0] == q], c['bf16'])) for q in pubs]
            row = {'labels': tag, 'arm': arm, 'model': m}
            for p in PRECISIONS:
                tp, fp, fn, sel, cr, cl = agg[p]
                row.update({f'{p}_value': val[p], f'{p}_ci_low': ci[p][0], f'{p}_ci_high': ci[p][1]})
                if arm != 'C':
                    row.update({f'{p}_precision': tp / (tp + fp) if tp + fp else float('nan'),
                                f'{p}_recall': tp / (tp + fn) if tp + fn else float('nan'),
                                f'{p}_selected': sel})
                else:
                    row.update({f'{p}_choices_labelled': cl})
            pubd = [x for x in pubd if x == x]  # publishers without labelled decisions drop out
            row.update({'metric': 'top1_relevance' if arm == 'C' else 'F1',
                        'nf4_minus_bf16': val['nf4'] - val['bf16'], 'diff_ci_low': dci[0], 'diff_ci_high': dci[1],
                        'diff_p_signflip_publishers': sign_p(pubd), 'publishers_used': len(pubd),
                        'publishers_positive': sum(x > 0 for x in pubd), 'publishers_negative': sum(x < 0 for x in pubd)})
            res.append(row)
    return res


def D_window(S, targets):
    if not targets: return None
    return sum(float(t in S[t]) - sum(float(t in S[e]) for e in range(8) if e != t) / 7 for t in targets) / len(targets)


def stratified(g, wins, tag):
    res = []
    for arm in ARMS:
        for m in MODELS:
            pubdelta = {}
            for stratum, want in (('all_labelled', None), ('ai_relevant', 1), ('ai_irrelevant', 0)):
                per = {p: defaultdict(lambda: defaultdict(list)) for p in PRECISIONS + ('delta',)}
                for w in wins:
                    tg = [t for t in range(8) if (w, t) in g and (want is None or g[(w, t)] == want)]
                    d = {p: D_window({k: dec[(arm, m, p, w, k)] for k in range(8)}, tg) for p in PRECISIONS}
                    if d['bf16'] is None: continue
                    pub, rep = win[w]
                    for p in PRECISIONS: per[p][pub][rep].append(d[p])
                    per['delta'][pub][rep].append(d['nf4'] - d['bf16'])
                def pe(x):
                    return {pub: sum(sum(v) / len(v) for v in reps.values()) / len(reps) for pub, reps in x.items()}
                pd = pe(per['delta']); pubdelta[stratum] = pd
                res.append({'labels': tag, 'arm': arm, 'model': m, 'stratum': stratum,
                            'bf16_D_pp': 100 * sum(pe(per['bf16']).values()) / len(pd),
                            'nf4_D_pp': 100 * sum(pe(per['nf4']).values()) / len(pd),
                            'nf4_minus_bf16_pp': 100 * sum(pd.values()) / len(pd), 'publishers': len(pd),
                            'publishers_positive': sum(v > 0 for v in pd.values()),
                            'p_exact_signflip': sign_p(pd.values())})
            common = sorted(set(pubdelta['ai_irrelevant']) & set(pubdelta['ai_relevant']))
            dd = [pubdelta['ai_irrelevant'][q] - pubdelta['ai_relevant'][q] for q in common]
            res.append({'labels': tag, 'arm': arm, 'model': m, 'stratum': 'irrelevant_minus_relevant',
                        'nf4_minus_bf16_pp': 100 * sum(dd) / len(dd), 'publishers': len(dd),
                        'publishers_positive': sum(v > 0 for v in dd), 'p_exact_signflip': sign_p(dd)})
    return res


def flips(g, wins, tag):
    res = []
    for arm in ARMS:
        for m in MODELS:
            cnt = defaultdict(int)
            for w in wins:
                for k in range(8):
                    b, n = dec[(arm, m, 'bf16', w, k)], dec[(arm, m, 'nf4', w, k)]
                    for t in range(8):
                        y = g.get((w, t))
                        if y is None: continue
                        pos = 'on' if t == k else 'off'
                        cnt[(pos, 'pairs')] += 1; cnt[(pos, 'relevant_pairs')] += y
                        if (t in b) != (t in n):
                            kind = 'added' if t in n else 'removed'
                            cnt[(pos, f"{kind}_{'relevant' if y else 'irrelevant'}")] += 1
            for pos in ('on', 'off'):
                r = {'labels': tag, 'arm': arm, 'model': m, 'position': pos + '_example',
                     'pairs': cnt[(pos, 'pairs')], 'relevant_share_of_pairs': cnt[(pos, 'relevant_pairs')] / cnt[(pos, 'pairs')]}
                for kind in ('added_relevant', 'added_irrelevant', 'removed_relevant', 'removed_irrelevant'):
                    r[kind] = cnt[(pos, kind)]
                ad = r['added_relevant'] + r['added_irrelevant']
                r['relevant_share_of_added'] = r['added_relevant'] / ad if ad else float('nan')
                r['net_added_relevant'] = r['added_relevant'] - r['removed_relevant']
                r['net_added_irrelevant'] = r['added_irrelevant'] - r['removed_irrelevant']
                res.append(r)
    return res


def chosen_k_relevance(g, wins):
    """Arm C: relevance of the chosen sentence when it is / is not the shown index."""
    res = []
    for m in MODELS:
        for p in PRECISIONS:
            c = {True: [0, 0], False: [0, 0]}
            for w in wins:
                for k in range(8):
                    (t,) = tuple(dec[('C', m, p, w, k)])
                    y = g.get((w, t))
                    if y is None: continue
                    c[t == k][0] += y; c[t == k][1] += 1
            res.append({'model': m, 'precision': p, 'choices_on_example': c[True][1],
                        'relevance_on_example': c[True][0] / c[True][1] if c[True][1] else float('nan'),
                        'choices_off_example': c[False][1],
                        'relevance_off_example': c[False][0] / c[False][1] if c[False][1] else float('nan')})
    return res


def dump(name, rs):
    with (a.out / name).open('w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rs for k in r)))
        wr.writeheader(); wr.writerows(rs)


allw = sorted(win); subw = sorted(subset)
rng = random.Random(SEED)
g0 = gold_map('primary')
Q = quality(g0, allw, rng, 'primary'); dump('quality.csv', Q)
S = stratified(g0, allw, 'primary'); dump('stratified.csv', S)
Fl = flips(g0, allw, 'primary'); dump('flips.csv', Fl)
CK = chosen_k_relevance(g0, allw); dump('armC_chosen_index_relevance.csv', CK)
sens = []
for mode, wins, tag in [] if a.partial else (('U0', allw, 'U_as_0'), ('U1', allw, 'U_as_1'), ('conf', allw, 'high_medium_confidence_only'),
                        ('primary', subw, 'human_subset_36_windows')):
    g = gold_map(mode)
    for r in quality(g, wins, random.Random(SEED), tag): sens.append({**r, 'kind': 'quality'})
    for r in stratified(g, wins, tag): sens.append({**r, 'kind': 'stratified'})
dump('sensitivity.csv', sens)
counts = defaultdict(int)
for r in rows: counts[r['label']] += 1
conf = defaultdict(int)
for r in rows: conf[(r['label'], r['confidence'])] += 1
json.dump({'status': ('EXPLORATORY_AI_GENERATED_LABELS_NOT_GROUND_TRUTH' if not a.partial else 'LABELLED_SUBSET'), 'labels_file': a.labels.name,
           'label_counts': counts, 'label_confidence_counts': {f'{k[0]}|{k[1]}': v for k, v in conf.items()},
           'revised_slots': sum(int(r.get('revised_before_export', 0) or 0) for r in rows), 'label_column': a.label_column, 'labelled_slots': len(rows),
           'bootstrap': {'draws': BOOT, 'seed': SEED, 'scheme': 'publisher then report, percentile'},
           'quality': Q, 'stratified': S, 'flips': Fl, 'armC_chosen_index_relevance': CK},
          (a.out / 'summary.json').open('w'), indent=1, default=float)
print('AI_LABEL_ANALYSIS_DONE', a.out)
