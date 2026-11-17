#!/usr/bin/env python3
"""Restore the text-bearing v2.1.6 reference archive needed by the frozen v2.2.1 code.

The public release omits report text. The v2.2.1 package
(src/v221_mechanism) expects reference/ThreatStudy_v216_Complete_Results.zip,
which contains outputs/prepared/inputs.jsonl (report sentences).

Two ways to restore it:

1. --original-zip PATH   the exact archive from the author (research use).
   It is verified against the frozen SHA-256 86e10189...; all frozen-release
   checks, CPU tests and GPU inference then work unchanged.

2. --inputs PATH         only the original inputs.jsonl (e.g. rebuilt from the
   CZLi/apt-reports dataset with src/v216_inference). Its hash is verified
   against the frozen manifest; an archive with identical members is rebuilt
   from the redacted archive. Zip container bytes differ, so the frozen
   release_check() in v22core.gpu_handoff will (correctly) refuse to authorise
   GPU runs, but text-dependent CPU tests run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "src/v221_mechanism/reference/ThreatStudy_v216_Complete_Results.zip"
FROZEN_ARCHIVE_SHA = "86e10189ae32f7308ffac800e8af547c509e4efb3c2ca39d7ab9980572b60500"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--original-zip", type=Path)
    g.add_argument("--inputs", type=Path)
    a = ap.parse_args()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if a.original_zip:
        got = sha(a.original_zip.read_bytes())
        if got != FROZEN_ARCHIVE_SHA:
            raise SystemExit("ARCHIVE_HASH_MISMATCH " + got)
        shutil.copy2(a.original_zip, TARGET)
        print("restored exact frozen archive ->", TARGET)
        return
    raw = a.inputs.read_bytes()
    frozen_inputs = json.loads((ROOT / "data/prepared/manifest.json").read_text())["input_sha256"]
    if sha(raw) != frozen_inputs:
        raise SystemExit("INPUT_HASH_MISMATCH: not the frozen inputs.jsonl")
    red = ROOT / "checkpoints/v216_armA_results_redacted.zip"
    with zipfile.ZipFile(red) as z, zipfile.ZipFile(TARGET, "w", zipfile.ZIP_DEFLATED) as o:
        for info in z.infolist():
            if info.filename == "outputs/prepared/REDACTION.json":
                continue
            if info.filename == "outputs/prepared/inputs_redacted.jsonl":
                o.writestr("outputs/prepared/inputs.jsonl", raw)
                continue
            o.writestr(info, z.read(info.filename))
    print("rebuilt member-identical archive ->", TARGET)
    print("note: container hash differs from frozen", FROZEN_ARCHIVE_SHA[:12], "- GPU authorisation will refuse it by design")


if __name__ == "__main__":
    main()
