#!/usr/bin/env python3
"""One-command reproduction of every reported statistic from the released checkpoints.

Standard library only; about 15 s on a laptop. Steps:
  1. verify SHA-256 of every release file (SHA256SUMS)
  2. Arm A (v2.1.6): recompute 6,912 records -> effects, exact p, Holm
  3. Arms B/C (v2.2.1): run the independent auditor on 14,256 records
  4. compare the auditor outputs with results/ byte for byte

    python3 reproduce/reproduce_all.py --out results_rerun
"""
from __future__ import annotations

import argparse
import filecmp
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*args: str) -> None:
    print("\n$", " ".join(args), flush=True)
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    out = a.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit("OUTPUT_DIRECTORY_NOT_EMPTY")
    run("reproduce/verify_release.py")
    run("reproduce/recompute_armA.py", "--out", str(out / "armA"))
    run("reproduce/run_audit_v221.py", "--out", str(out / "audit_v221"))
    names = ["independent_v221_results.json", "independent_window_effects.csv",
             "independent_publisher_effects.csv", "independent_arm_comparisons.csv",
             "independent_arm_comparisons.json"]
    bad = [n for n in names if not filecmp.cmp(out / "audit_v221" / n, ROOT / "results/armBC_v221" / n, shallow=False)]
    if bad:
        raise SystemExit("MISMATCH_WITH_RELEASED_RESULTS " + ", ".join(bad))
    print("\nALL_REPRODUCTION_CHECKS_PASS: Arm A effects match archive; Arm B/C audit outputs byte-identical")


if __name__ == "__main__":
    main()
