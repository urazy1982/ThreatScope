#!/usr/bin/env python3
"""Run the independent v2.2.1 auditor (Arms B and C, replay check) from the release archives.

Standard library only. This wrapper replaces the original bundle wrapper,
which extracted the v2.1.6 baseline from a code release that also contained
report text. Here the text-free baseline archive is used directly; the two
auditor scripts in reproduce/audit_v221/ are copied unchanged.

Usage:
    python3 reproduce/run_audit_v221.py --out results_rerun/audit_v221   # must be new or empty
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def safe_extract(z: zipfile.ZipFile, dest: Path) -> None:
    base = dest.resolve()
    for entry in z.infolist():
        target = (base / entry.filename).resolve()
        if not target.is_relative_to(base):
            raise ValueError("unsafe zip entry: " + entry.filename)
    z.extractall(base)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-zip", type=Path, default=ROOT / "checkpoints/v221_armBC_and_replay_results.zip")
    ap.add_argument("--baseline-zip", type=Path, default=ROOT / "checkpoints/v216_armA_results_redacted.zip")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise SystemExit("OUTPUT_DIRECTORY_NOT_EMPTY: use a new empty directory")
    with zipfile.ZipFile(a.results_zip) as z:
        if z.testzip() is not None:
            raise SystemExit("CORRUPT_RESULTS_ZIP")
        safe_extract(z, out)
    shutil.copy2(a.baseline_zip, out / "baseline_v216.zip")
    for name in ("independent_recompute.py", "compare_arms.py"):
        shutil.copy2(ROOT / "reproduce/audit_v221" / name, out / name)
    subprocess.run([sys.executable, str(out / "independent_recompute.py")], cwd=out, check=True)
    subprocess.run([sys.executable, str(out / "compare_arms.py")], cwd=out, check=True)
    print("INDEPENDENT_V221_AUDIT_SUCCESS", out)


if __name__ == "__main__":
    main()
