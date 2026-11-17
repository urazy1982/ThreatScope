#!/usr/bin/env python3
"""Analyse human relevance labels for the pre-declared 36-window subset.

Standard library only (openpyxl is used if label files are .xlsx).

Outputs (in --out):
  agreement.json             Cohen's kappa, raw agreement, prevalence (two annotators)
  disagreements.csv          items to adjudicate
  decision_quality.csv       per arm x model x precision: precision/recall/F1 (A, B),
                             top-1 relevance (C); publisher-cluster bootstrap CIs
  stratified_interaction.csv example-index interaction computed separately on
                             gold-relevant and gold-irrelevant target sentences,
                             NF4-BF16 difference and exact publisher sign-flip p
  flips.csv                  BF16->NF4 decision changes split by gold label,
                             on-example vs off-example targets
  annotation_results.json    everything above, machine readable
  SUMMARY.md                 short human-readable summary

Usage:
  python3 annotation/analyze_annotation.py --labels labels/A.xlsx labels/B.xlsx \
      [--adjudication labels/adjudication.csv] --out results_rerun/annotation
  python3 annotation/analyze_annotation.py --selftest --out /tmp/selftest   # synthetic labels, code check only
"""
from __future__ import annotations

import argparse
import csv
import io
import itertools
import json
import random
import zipfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MODELS = ("Qwen/Qwen2.5-3B-Instruct", "meta-llama/Llama-3.2-3B-Instruct",
          "mistralai/Mistral-7B-Instruct-v0.3")
PRECISIONS = ("bf16", "nf4")
ARMS = ("A", "B", "C")
BOOT = 2000
SEED = 20261113


def run_dir(m: str) -> str:
    return m.split("/")[-1].lower().replace(".", "-")


# ---------------------------------------------------------------- labels
def read_label_file(p: Path) -> dict[str, int]:
    rows: list[dict] = []
    if p.suffix.lower() == ".xlsx":
        import openpyxl
        ws = openpyxl.load_workbook(p, read_only=True, data_only=True)["label_here"]
        it = ws.iter_rows(values_only=True)
        hdr = [str(h) for h in next(it)]
        rows = [dict(zip(hdr, r)) for r in it]
    else:
        rows = list(csv.DictReader(p.open(encoding="utf-8")))
    out = {}
    for r in rows:
        if not r.get("item_id"):
            continue
        v = str(r.get("relevant", "")).strip()
        if v.endswith(".0"):
            v = v[:-2]
        if v not in ("0", "1"):
            raise SystemExit(f"{p.name}: item {r['item_id']} has no valid 0/1 label ({v!r})")
        out[str(r["item_id"])] = int(v)
    return out


def kappa(a: list[int], b: list[int]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


# ---------------------------------------------------------------- decisions
def load_decisions(windows: set[str], a_zip: Path, bc_zip: Path):
    dec = {}
    with zipfile.ZipFile(a_zip) as z:
        for m in MODELS:
            for p in PRECISIONS:
                for k in range(8):
                    for w in windows:
                        r = json.loads(z.read(f"outputs/runs/{run_dir(m)}/{p}/example_{k}/{w}.json"))
                        dec[("A", m, p, w, k)] = set(r["indices"]) if r["valid"] else set()
    with zipfile.ZipFile(bc_zip) as z:
        for arm in ("B", "C"):
            for m in MODELS:
                for p in PRECISIONS:
                    for k in range(8):
                        for w in windows:
                            r = json.loads(z.read(f"outputs_v221/runs/{arm}/{run_dir(m)}/{p}/example_{k}/{w}.json"))
                            assert r["valid"] and r["anchor"] == k
                            dec[(arm, m, p, w, k)] = set(r["indices"])
    return dec


# ---------------------------------------------------------------- statistics
def sign_flip_p(xs) -> float:
    xs = list(xs)
    obs = abs(sum(xs))
    return sum(abs(sum(a * s for a, s in zip(xs, sg))) >= obs - 1e-12
               for sg in itertools.product((-1, 1), repeat=len(xs))) / 2 ** len(xs)


def prf(cells):
    tp = sum(c[0] for c in cells); fp = sum(c[1] for c in cells); fn = sum(c[2] for c in cells)
    pr = tp / (tp + fp) if tp + fp else float("nan")
    rc = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * pr * rc / (pr + rc) if pr == pr and rc == rc and pr + rc else float("nan")
    return pr, rc, f1


def cluster_boot(by_pub: dict, stat, rng: random.Random):
    pubs = sorted(by_pub)
    vals = []
    for _ in range(BOOT):
        sample = []
        for p in (rng.choice(pubs) for _ in pubs):
            ws = by_pub[p]
            sample.extend(rng.choice(ws) for _ in ws)
        v = stat(sample)
        if v == v:
            vals.append(v)
    vals.sort()
    if not vals:
        return float("nan"), float("nan")
    return vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))]


def stratified_D(sel: dict[int, set[int]], targets: list[int]) -> float | None:
    if not targets:
        return None
    tot = 0.0
    for t in targets:
        on = float(t in sel[t])
        off = sum(float(t in sel[e]) for e in range(8) if e != t) / 7
        tot += on - off
    return tot / len(targets)


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", nargs="*", type=Path, default=[])
    ap.add_argument("--adjudication", type=Path, default=None)
    ap.add_argument("--a-zip", type=Path, default=ROOT / "checkpoints/v216_armA_results_redacted.zip")
    ap.add_argument("--bc-zip", type=Path, default=ROOT / "checkpoints/v221_armBC_and_replay_results.zip")
    ap.add_argument("--selftest", action="store_true", help="use synthetic random labels (code check only)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    items = list(csv.DictReader((HERE / "subset_items.csv").open()))
    wins = {r["window_id"]: r for r in csv.DictReader((HERE / "subset_windows.csv").open())}
    item_of = {(r["window_id"], int(r["sentence_index"])): r["item_id"] for r in items}

    # ---- labels and gold
    if a.selftest:
        rng = random.Random(1)
        ann = {"SYN_A": {r["item_id"]: int(rng.random() < 0.55) for r in items}}
        ann["SYN_B"] = {k: (v if rng.random() < 0.85 else 1 - v) for k, v in ann["SYN_A"].items()}
    else:
        if not a.labels:
            raise SystemExit("give --labels (one or two files) or --selftest")
        ann = {p.stem: read_label_file(p) for p in a.labels}
    for name, lab in ann.items():
        missing = {r["item_id"] for r in items} - set(lab)
        if missing:
            raise SystemExit(f"{name}: {len(missing)} items unlabeled, e.g. {sorted(missing)[:3]}")
    names = list(ann)
    agreement = None
    gold, gold_basis = {}, ""
    if len(names) >= 2:
        A, B = ann[names[0]], ann[names[1]]
        ids = [r["item_id"] for r in items]
        xa, xb = [A[i] for i in ids], [B[i] for i in ids]
        agreement = {"annotators": names[:2], "n": len(ids),
                     "raw_agreement": sum(x == y for x, y in zip(xa, xb)) / len(ids),
                     "cohen_kappa": kappa(xa, xb),
                     "prevalence_relevant": {names[0]: sum(xa) / len(ids), names[1]: sum(xb) / len(ids)},
                     "disagreements": sum(x != y for x, y in zip(xa, xb))}
        with (a.out / "disagreements.csv").open("w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(["item_id", names[0], names[1]])
            wr.writerows([i, A[i], B[i]] for i in ids if A[i] != B[i])
        adj = {}
        if a.adjudication:
            adj = {r["item_id"]: int(r["relevant"]) for r in csv.DictReader(a.adjudication.open())}
        for i in ids:
            if A[i] == B[i]:
                gold[i] = A[i]
            elif i in adj:
                gold[i] = adj[i]
        unresolved = len(ids) - len(gold)
        gold_basis = ("adjudicated" if unresolved == 0 else
                      f"agreement-only ({unresolved} unadjudicated disagreements excluded)")
    else:
        gold = dict(ann[names[0]])
        gold_basis = "single annotator (no agreement statistic)"

    # ---- decisions
    dec = load_decisions(set(wins), a.a_zip, a.bc_zip)
    rng = random.Random(SEED)
    quality, strat, flips = [], [], []
    for arm in ARMS:
        for m in MODELS:
            per_window = {}
            for p in PRECISIONS:
                by_pub = defaultdict(list)
                for w, info in wins.items():
                    cells = []
                    for k in range(8):
                        chosen = dec[(arm, m, p, w, k)]
                        for t in range(8):
                            g = gold.get(item_of[(w, t)])
                            if g is None:
                                continue
                            s = t in chosen
                            cells.append((int(s and g == 1), int(s and g == 0), int((not s) and g == 1), int(s)))
                    by_pub[info["publisher"]].append(cells)
                    per_window[(p, w)] = cells
                flat = [c for ws in by_pub.values() for cells in ws for c in cells]
                if arm == "C":
                    stat = lambda S: (lambda c: sum(x[0] for x in c) / max(1, sum(x[3] for x in c)))([x for cl in S for x in cl])
                    top1 = stat([cl for ws in by_pub.values() for cl in ws])
                    lo, hi = cluster_boot(by_pub, stat, rng)
                    quality.append({"arm": arm, "model": m, "precision": p, "metric": "top1_relevance",
                                    "value": top1, "ci_low": lo, "ci_high": hi,
                                    "selected": sum(x[3] for x in flat)})
                else:
                    pr, rc, f1 = prf(flat)
                    lo, hi = cluster_boot(by_pub, lambda S: prf([x for cl in S for x in cl])[2], rng)
                    quality.append({"arm": arm, "model": m, "precision": p, "metric": "F1", "value": f1,
                                    "ci_low": lo, "ci_high": hi, "precision_score": pr, "recall": rc,
                                    "selection_rate": sum(x[3] for x in flat) / len(flat)})
            # gold-stratified example-index interaction, NF4 - BF16
            for stratum, want in (("all", None), ("gold_relevant", 1), ("gold_irrelevant", 0)):
                pubvals = defaultdict(list)
                for w, info in wins.items():
                    tg = [t for t in range(8) if (g := gold.get(item_of[(w, t)])) is not None and (want is None or g == want)]
                    d = {p: stratified_D({k: dec[(arm, m, p, w, k)] for k in range(8)}, tg) for p in PRECISIONS}
                    if d["bf16"] is not None:
                        pubvals[info["publisher"]].append(d["nf4"] - d["bf16"])
                pub = {k: sum(v) / len(v) for k, v in pubvals.items()}
                strat.append({"arm": arm, "model": m, "stratum": stratum,
                              "nf4_minus_bf16_pp": 100 * sum(pub.values()) / len(pub) if pub else float("nan"),
                              "publishers": len(pub), "positive_publishers": sum(v > 0 for v in pub.values()),
                              "p_exact_signflip": sign_flip_p(pub.values()) if pub else float("nan")})
            # BF16 -> NF4 flips
            cnt = defaultdict(int)
            for w in wins:
                for k in range(8):
                    b, n = dec[(arm, m, "bf16", w, k)], dec[(arm, m, "nf4", w, k)]
                    for t in range(8):
                        g = gold.get(item_of[(w, t)])
                        if g is None:
                            continue
                        pos = "on_example" if t == k else "off_example"
                        cnt[(pos, "pairs")] += 1
                        if (t in b) != (t in n):
                            kind = "nf4_added" if t in n else "nf4_removed"
                            cnt[(pos, f"{kind}_{'relevant' if g else 'irrelevant'}")] += 1
            for pos in ("on_example", "off_example"):
                row = {"arm": arm, "model": m, "target_position": pos, "pairs": cnt[(pos, "pairs")]}
                for kind in ("nf4_added_relevant", "nf4_added_irrelevant", "nf4_removed_relevant", "nf4_removed_irrelevant"):
                    row[kind] = cnt[(pos, kind)]
                row["net_false_positives_added"] = row["nf4_added_irrelevant"] - row["nf4_removed_irrelevant"]
                row["net_true_positives_added"] = row["nf4_added_relevant"] - row["nf4_removed_relevant"]
                flips.append(row)

    def dump(name, rows):
        with (a.out / name).open("w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
            wr.writeheader()
            wr.writerows(rows)
    dump("decision_quality.csv", quality)
    dump("stratified_interaction.csv", strat)
    dump("flips.csv", flips)
    out = {"status": "SYNTHETIC_SELFTEST_NOT_RESULTS" if a.selftest else "ANNOTATION_ANALYSIS",
           "gold_basis": gold_basis, "gold_items": len(gold), "gold_prevalence": sum(gold.values()) / len(gold),
           "agreement": agreement, "decision_quality": quality, "stratified_interaction": strat, "flips": flips,
           "bootstrap": {"draws": BOOT, "seed": SEED, "note": "publisher-then-window cluster bootstrap; descriptive"}}
    (a.out / "annotation_results.json").write_text(json.dumps(out, indent=2) + "\n")
    if agreement:
        (a.out / "agreement.json").write_text(json.dumps(agreement, indent=2) + "\n")

    lines = [f"# Labeled-subset analysis ({out['status']})", "",
             f"Gold standard: {gold_basis}; {len(gold)} items; prevalence relevant = {out['gold_prevalence']:.3f}."]
    if agreement:
        lines.append(f"Agreement: raw {agreement['raw_agreement']:.3f}, Cohen's kappa {agreement['cohen_kappa']:.3f} "
                     f"({agreement['disagreements']} disagreements).")
    lines += ["", "| Arm | Model | Stratum | NF4-BF16 (pp) | publishers + | exact p |", "|---|---|---|---:|---:|---:|"]
    for r in strat:
        lines.append(f"| {r['arm']} | {r['model'].split('/')[-1]} | {r['stratum']} | {r['nf4_minus_bf16_pp']:+.2f} | "
                     f"{r['positive_publishers']}/{r['publishers']} | {r['p_exact_signflip']:.4f} |")
    (a.out / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
