#!/usr/bin/env python3
"""Independent recomputation of the Arm A (v2.1.6, free generation) results.

Standard library only. Reads the text-free checkpoint archive
``checkpoints/v216_armA_results_redacted.zip`` and recomputes, for each model,
the publisher-equal, report-equal NF4-minus-BF16 example-index interaction,
the exact two-sided publisher sign-flip p value (2^9 sign patterns) and the
Holm adjustment across the three models. The result is compared against the
archived ``outputs/analysis/model_summary.csv``.

Estimand (per window, per precision):
    D = mean over target index t of
        [ 1{t selected | example index = t}
          - mean_{e != t} 1{t selected | example index = e} ]
Invalid outputs select nothing (primary, intention-to-treat definition).

Usage:
    python3 reproduce/recompute_armA.py --out results_rerun/armA
    python3 reproduce/recompute_armA.py --out ... --inputs /path/to/original/inputs.jsonl
The optional --inputs file (not distributed; contains report text) is checked
against the frozen input hash in data/prepared/manifest.json.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
import math
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ("Qwen/Qwen2.5-3B-Instruct", "meta-llama/Llama-3.2-3B-Instruct",
          "mistralai/Mistral-7B-Instruct-v0.3")
PRECISIONS = ("bf16", "nf4")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def enc(v) -> bytes:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def run_dir(model: str) -> str:
    return model.split("/")[-1].lower().replace(".", "-")


def interaction(sel: dict[int, set[int]]) -> float:
    if set(sel) != set(range(8)):
        raise AssertionError("incomplete example indices")
    total = 0.0
    for t in range(8):
        on = float(t in sel[t])
        off = sum(float(t in sel[e]) for e in range(8) if e != t) / 7
        total += (on - off) / 8
    return total


def sign_flip_p(values) -> float:
    xs = list(values)
    obs = abs(sum(xs))
    hits = sum(abs(sum(a * s for a, s in zip(xs, signs))) >= obs - 1e-12
               for signs in itertools.product((-1, 1), repeat=len(xs)))
    return hits / 2 ** len(xs)


def holm(p: dict) -> dict:
    out, floor = {}, 0.0
    for rank, (k, v) in enumerate(sorted(p.items(), key=lambda kv: kv[1])):
        floor = max(floor, min(1.0, v * (len(p) - rank)))
        out[k] = floor
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, default=ROOT / "checkpoints/v216_armA_results_redacted.zip")
    ap.add_argument("--windows", type=Path, default=ROOT / "data/prepared/inputs_redacted.jsonl")
    ap.add_argument("--manifest", type=Path, default=ROOT / "data/prepared/manifest.json")
    ap.add_argument("--inputs", type=Path, default=None, help="optional original inputs.jsonl")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(a.manifest.read_text())
    if a.inputs is not None:
        got = sha(a.inputs.read_bytes())
        if got != manifest["input_sha256"]:
            raise SystemExit(f"INPUT_HASH_MISMATCH {got}")
        print("original inputs.jsonl verified against frozen manifest")

    windows = {}
    for line in a.windows.read_text().splitlines():
        if line.strip():
            w = json.loads(line)
            windows[w["window_id"]] = w
    assert len(windows) == 144
    assert len({w["report_id"] for w in windows.values()}) == 72
    assert len({w["source"] for w in windows.values()}) == 9

    sel = defaultdict(dict)       # (model, prec, window) -> {anchor: set}
    invalid = defaultdict(int)
    with zipfile.ZipFile(a.archive) as z:
        if z.testzip() is not None:
            raise SystemExit("CORRUPT_ARCHIVE")
        names = set(z.namelist())
        n = 0
        for m in MODELS:
            for p in PRECISIONS:
                for k in range(8):
                    for wid, w in windows.items():
                        fn = f"outputs/runs/{run_dir(m)}/{p}/example_{k}/{wid}.json"
                        if fn not in names:
                            raise AssertionError("missing " + fn)
                        rec = json.loads(z.read(fn))
                        body = {kk: vv for kk, vv in rec.items() if kk != "record_sha256"}
                        if rec["record_sha256"] != sha(enc(body)):
                            raise AssertionError("record hash mismatch " + fn)
                        if rec["raw"] is not None and rec["raw_sha256"] != sha(enc(rec["raw"])):
                            raise AssertionError("raw hash mismatch " + fn)
                        assert rec["model"] == m and rec["precision"] == p and rec["anchor"] == k
                        assert rec["input_sha256"] == w["input_sha256"], "window identity mismatch " + fn
                        idx = set(rec["indices"]) if rec["valid"] else set()
                        if not rec["valid"]:
                            invalid[(m, p)] += 1
                        sel[(m, p, wid)][k] = idx
                        n += 1
        archived = list(csv.DictReader(io.StringIO(z.read("outputs/analysis/model_summary.csv").decode())))
    assert n == 6912, n

    window_rows, pvals, results = [], {}, []
    for m in MODELS:
        by_pub = defaultdict(lambda: defaultdict(list))
        for wid, w in windows.items():
            d = {p: interaction(sel[(m, p, wid)]) for p in PRECISIONS}
            diff = d["nf4"] - d["bf16"]
            by_pub[w["source"]][w["report_id"]].append(diff)
            window_rows.append({"model": m, "publisher": w["source"], "report_id": w["report_id"],
                                "window_id": wid, "bf16_D": d["bf16"], "nf4_D": d["nf4"], "difference": diff})
        pub = {s: sum(sum(v) / len(v) for v in reps.values()) / len(reps) for s, reps in by_pub.items()}
        effect = sum(pub.values()) / len(pub)
        pvals[m] = sign_flip_p(pub.values())
        results.append({"model": m, "effect": effect, "p_exact": pvals[m],
                        "positive_publishers": sum(v > 0 for v in pub.values()),
                        "negative_publishers": sum(v < 0 for v in pub.values()),
                        "invalid_bf16": invalid[(m, "bf16")], "invalid_nf4": invalid[(m, "nf4")],
                        "publisher_effects": pub})
    h = holm(pvals)
    for r in results:
        r["p_holm_3"] = h[r["model"]]
        old = next(x for x in archived if x["model"] == r["model"])
        assert math.isclose(r["effect"], float(old["source_equal_interaction"]), abs_tol=1e-12), r["model"]
        assert math.isclose(r["p_exact"], float(old["source_signflip_two_sided_p"]), abs_tol=1e-15)
        assert math.isclose(r["p_holm_3"], float(old["holm_p"]), abs_tol=1e-15)
        assert r["invalid_bf16"] == int(old["invalid_bf16"]) and r["invalid_nf4"] == int(old["invalid_nf4"])

    (a.out / "armA_results.json").write_text(json.dumps(
        {"status": "ARM_A_RECOMPUTE_PASS", "records_verified": n, "results": results}, indent=2) + "\n")
    with (a.out / "armA_window_effects.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(window_rows[0]))
        wr.writeheader()
        wr.writerows(window_rows)
    for r in results:
        print(f"A {r['model'].split('/')[-1]:<26} effect={100*r['effect']:+.2f} pp  "
              f"p={r['p_exact']:.5f}  Holm3={r['p_holm_3']:.5f}  invalid BF16/NF4={r['invalid_bf16']}/{r['invalid_nf4']}")
    print("ARM_A_RECOMPUTE_PASS", n, "records")


if __name__ == "__main__":
    main()
