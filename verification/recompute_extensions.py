#!/usr/bin/env python3
"""Extensions E1-E4 (ThreatScope v1.1.0): recompute every quantity reported in the manuscript from the
text-free decision records and the raw E3/E4 checkpoints, independently of the release's own analysis
scripts (written separately for the manuscript audit; standard library only).

Usage: python3 verification/recompute_extensions.py [release_root] [output.json]

Estimand D is the manuscript's Eq. (1). Aggregation window -> report -> publisher with equal
weights unless stated. Exact two-sided publisher sign-flip test (sign ties within 1e-9 treated as 0).
"""
import csv, glob, itertools, json, random
from collections import defaultdict
from pathlib import Path
from statistics import mean

import sys
REL = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
EXT = REL / 'extensions'
EV = EXT / 'E5_synthesis' / 'evidence'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else REL / 'verification' / 'recomputed_extensions.json'
TOL = 1e-9
SHORT = {'Qwen/Qwen2.5-3B-Instruct': 'Qwen', 'meta-llama/Llama-3.2-3B-Instruct': 'Llama',
         'mistralai/Mistral-7B-Instruct-v0.3': 'Mistral'}


def D(sel):
    return mean((t in sel[t]) - mean(t in sel[e] for e in range(8) if e != t) for t in range(8))


def p2(v):
    o = abs(mean(v))
    return sum(abs(mean(a * b for a, b in zip(v, s))) >= o - TOL
               for s in itertools.product((1, -1), repeat=len(v))) / 2 ** len(v)


def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); out = [0.0] * len(ps); run = 0.0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (len(ps) - r) * ps[i])); out[i] = run
    return out


def signs(v):
    return {'pos': sum(x > TOL for x in v), 'neg': sum(x < -TOL for x in v), 'zero': sum(abs(x) <= TOL for x in v)}


def to_pub(vals, meta, hier=True):
    if hier:
        rep = defaultdict(list)
        for w, x in vals.items(): rep[meta[w]].append(x)
        pub = defaultdict(list)
        for (p, _), xs in rep.items(): pub[p].append(mean(xs))
    else:
        pub = defaultdict(list)
        for w, x in vals.items(): pub[meta[w][0]].append(x)
    return {p: mean(x) for p, x in pub.items()}


def boot(vals, meta, draws=10000, seed=20261116):
    """Descriptive hierarchical bootstrap: publishers, then reports within publisher."""
    tree = defaultdict(lambda: defaultdict(list))
    for w, x in vals.items(): tree[meta[w][0]][meta[w][1]].append(x)
    pubs = sorted(tree); rng = random.Random(seed); est = []
    for _ in range(draws):
        pv = []
        for p in (rng.choice(pubs) for _ in pubs):
            reps = sorted(tree[p]); pv.append(mean(mean(tree[p][r]) for r in (rng.choice(reps) for _ in reps)))
        est.append(mean(pv))
    est.sort()
    return [est[int(0.025 * draws)], est[int(0.975 * draws) - 1]]


def e2(meta_out):
    rows = list(csv.DictReader(open(EV / 'E2_per_prompt_decisions_2304.csv')))
    meta = {}; S = defaultdict(dict)
    for r in rows:
        w = r['window_id']; meta[w] = (r['publisher'], r['report_id'])
        for proc in ('greedy', 'scoring'):
            S[(w, r['precision'], proc)][int(r['prompt_digit_k'])] = {int(r[f'{proc}_choice'])}
    out = {'prompts': len(rows), 'windows': len(meta), 'publishers': len({m[0] for m in meta.values()})}
    pubD = {}
    for proc in ('greedy', 'scoring'):
        for pr in ('bf16', 'nf4'):
            out[f'{proc}_{pr}_D_pp'] = mean(to_pub({w: 100 * D(S[(w, pr, proc)]) for w in meta}, meta).values())
        pubD[proc] = to_pub({w: 100 * (D(S[(w, 'nf4', proc)]) - D(S[(w, 'bf16', proc)])) for w in meta}, meta)
        out[f'{proc}_delta_pp'] = mean(pubD[proc].values())
        out[f'{proc}_delta_p'] = p2(list(pubD[proc].values()))
    did = {p: pubD['greedy'][p] - pubD['scoring'][p] for p in pubD['greedy']}
    out.update(did_pp=mean(did.values()), did_p=p2(list(did.values())), did_signs=signs(list(did.values())),
               did_publisher_pp=did,
               agree_bf16=mean(r['greedy_choice'] == r['scoring_choice'] for r in rows if r['precision'] == 'bf16'),
               agree_nf4=mean(r['greedy_choice'] == r['scoring_choice'] for r in rows if r['precision'] == 'nf4'),
               did_ci_pp=boot({w: 100 * ((D(S[(w, 'nf4', 'greedy')]) - D(S[(w, 'bf16', 'greedy')]))
                                         - (D(S[(w, 'nf4', 'scoring')]) - D(S[(w, 'bf16', 'scoring')]))) for w in meta}, meta))
    meta_out.update(meta)
    return out


def e1(meta):
    rows = list(csv.DictReader(open(EV / 'E1_window_decisions_1728.csv')))
    cell = {(r['model'], r['precision'], r['condition'], r['window_id']):
            (r['valid'] == '1', set(json.loads(r['indices_json'])) if r['valid'] == '1' else set()) for r in rows}
    ham = lambda a, b: len(a ^ b) / 8
    out = {'records': len(rows), 'valid': sum(r['valid'] == '1' for r in rows), 'models': {}}
    prim_p = {}
    for mdl, sh in SHORT.items():
        cnt = {f'{pr}_{cd}': {'invalid': sum(not cell[(mdl, pr, cd, w)][0] for w in meta),
                              'valid_empty': sum(cell[(mdl, pr, cd, w)][0] and not cell[(mdl, pr, cd, w)][1] for w in meta)}
               for pr in ('bf16', 'nf4') for cd in ('N0', 'N1')}
        res = {'cells': cnt}
        for rule in ('as_run', 'cc_hier', 'itt_hier'):
            vals, lev = {}, {'N0': {}, 'N1': {}}
            for w in meta:
                c = {(pr, cd): cell[(mdl, pr, cd, w)] for pr in ('bf16', 'nf4') for cd in ('N0', 'N1')}
                if rule != 'itt_hier' and not all(x[0] for x in c.values()): continue
                for cd in ('N0', 'N1'): lev[cd][w] = 100 * ham(c[('bf16', cd)][1], c[('nf4', cd)][1])
                vals[w] = lev['N1'][w] - lev['N0'][w]
            hier = rule != 'as_run'
            pv = to_pub(vals, meta, hier)
            res[rule] = {'windows': len(vals), 'effect_pp': mean(pv.values()), 'p': p2(list(pv.values())),
                         'N0_pp': mean(to_pub(lev['N0'], meta, hier).values()), 'N1_pp': mean(to_pub(lev['N1'], meta, hier).values())}
        out['models'][sh] = res; prim_p[sh] = res['as_run']['p']
    for sh, h in zip(prim_p, holm(list(prim_p.values()))): out['models'][sh]['as_run']['p_holm3'] = h
    return out


def parse(raw):
    try:
        o = json.loads(raw.strip())
        xs = o['relevant'] if isinstance(o, dict) and set(o) == {'relevant'} else None
        if (not isinstance(xs, list) or len(set(xs)) != len(xs)
                or not all(isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 7 for x in xs)):
            return False, set()
        return True, set(xs)
    except Exception:
        return False, set()


def e34():
    recs, mism = {}, 0
    for f in glob.glob(str(EXT / 'E3_checkpoints/results/E3/*/*/example_*/*.json')) + \
             glob.glob(str(EXT / 'E4_checkpoints/results/E4/*/*/example_*/*.json')):
        d = json.load(open(f)); v, s = parse(d['raw'])
        rv = d['valid'] in (True, 'True'); ri = d['indices'] if isinstance(d['indices'], list) else json.loads(d['indices'])
        mism += (v != rv) or (v and s != set(ri))
        recs[(d['model'], d['precision'], d['window_id'], int(d['anchor']))] = (v, s)
    meta = {r['window_id']: (r['source'], r['report_id'])
            for r in csv.DictReader(open(EXT / 'E3_checkpoints/results/reports/E3_decisions_textfree.csv'))}
    alloc = defaultdict(set)
    for w, (p, r) in meta.items(): alloc[p].add(r)

    def eff(model, hi, lo, need=None):
        vals = {}
        for w in meta:
            if need and not all(recs[(model, p, w, k)][0] for p in need for k in range(8)): continue
            vals[w] = 100 * (D({k: recs[(model, hi, w, k)][1] for k in range(8)}) - D({k: recs[(model, lo, w, k)][1] for k in range(8)}))
        pv = to_pub(vals, meta)
        return vals, pv
    out = {'records': len(recs), 'parser_mismatches': mism, 'E3_generations': 6 * 8 * len(meta), 'E4_generations': 2 * 8 * len(meta), 'reports': len({r for _, r in meta.values()}), 'windows': len(meta),
           'publishers': len(alloc), 'allocation': {p: len(r) for p, r in sorted(alloc.items())}, 'E3': {}, 'E4': {}}
    inv = defaultdict(int)
    for (m, p, w, k), (v, _) in recs.items(): inv[(m, p)] += (not v)
    p3 = {}
    for mdl, sh in SHORT.items():
        vals, pv = eff(mdl, 'nf4', 'bf16'); v = list(pv.values())
        loo = [mean([x for q, x in pv.items() if q != d]) for d in pv]
        out['E3'][sh] = {'effect_pp': mean(v), 'p': p2(v), 'signs': signs(v), 'loo_min_pp': min(loo), 'loo_max_pp': max(loo),
                         'ci_pp': boot(vals, meta), 'publisher_pp': pv,
                         'bf16_D_pp': mean(to_pub({w: 100 * D({k: recs[(mdl, 'bf16', w, k)][1] for k in range(8)}) for w in meta}, meta).values()),
                         'nf4_D_pp': mean(to_pub({w: 100 * D({k: recs[(mdl, 'nf4', w, k)][1] for k in range(8)}) for w in meta}, meta).values()),
                         'bf16_invalid': inv[(mdl, 'bf16')], 'nf4_invalid': inv[(mdl, 'nf4')], 'calls_per_precision': 8 * len(meta)}
        p3[sh] = out['E3'][sh]['p']
    for sh, h in zip(p3, holm(list(p3.values()))): out['E3'][sh]['p_holm3'] = h
    p4 = {}
    for mdl, sh in list(SHORT.items())[:2]:
        vals, pv = eff(mdl, 'fp4', 'nf4'); v = list(pv.values())
        cvals, cpv = eff(mdl, 'fp4', 'nf4', need=('bf16', 'nf4', 'fp4'))
        bvals, bpv = eff(mdl, 'fp4', 'bf16')
        out['E4'][sh] = {'effect_pp': mean(v), 'p': p2(v), 'signs': signs(v), 'ci_pp': boot(vals, meta), 'publisher_pp': pv,
                         'fp4_D_pp': mean(to_pub({w: 100 * D({k: recs[(mdl, 'fp4', w, k)][1] for k in range(8)}) for w in meta}, meta).values()),
                         'fp4_invalid': inv[(mdl, 'fp4')], 'calls': 8 * len(meta), 'fp4_invalid_pct': 100 * inv[(mdl, 'fp4')] / (8 * len(meta)),
                         'cc_effect_pp': mean(cpv.values()), 'cc_p': p2(list(cpv.values())), 'cc_windows': len(cvals),
                         'fp4_minus_bf16_pp': mean(bpv.values()), 'fp4_minus_bf16_p': p2(list(bpv.values()))}
        p4[sh] = out['E4'][sh]['p']
    for sh, h in zip(p4, holm(list(p4.values()))): out['E4'][sh]['p_holm2'] = h
    return out


if __name__ == '__main__':
    meta = {}
    ext = {'E2': e2(meta)}
    ext['E1'] = e1(meta)
    ext['E34'] = e34()
    json.dump(ext, open(OUT, 'w'), indent=1, default=float)
    q = ext['E34']['E3']['Qwen']
    print('ext facts ok: E3 Qwen', round(q['effect_pp'], 4), q['p'], round(q['p_holm3'], 7), 'CI', [round(x, 2) for x in q['ci_pp']],
          '| E2 DID', round(ext['E2']['did_pp'], 4), ext['E2']['did_p'], '| parser mismatches', ext['E34']['parser_mismatches'])
