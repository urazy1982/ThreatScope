#!/usr/bin/env python3
"""Export a text-free source index (report_id -> publisher URL) from the frozen corpus.

Run once by the study author on the machine that holds the frozen
dataset/reports.json (72 reports, SHA-256 461682f3...). The output
data/report_sources.csv contains only identifiers, publisher names, original
URLs, archive paths and HTML hashes, so third parties can re-acquire the same
reports from CZLi/apt-reports or the publishers without this repository
redistributing any report text.

    python3 tools/export_report_sources.py --reports ~/threat-study/aptcorpus_v214_work/dataset/reports.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src/v216_inference"))
from crosscti.core import digest  # noqa: E402  (identical ID function used at preparation time)
from crosscti.prepare import canon  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=ROOT / "data/report_sources.csv")
    a = ap.parse_args()
    raw = a.reports.read_bytes()
    manifest = json.loads((ROOT / "data/prepared/manifest.json").read_text())
    if hashlib.sha256(raw).hexdigest() != manifest["dataset_sha256"]:
        raise SystemExit("DATASET_HASH_MISMATCH: not the frozen 72-report reports.json")
    cfg = json.loads((ROOT / "data/config/study.json").read_text())
    expected = {r["report_id"]: r["source"] for r in manifest["selected_reports"]}
    rows = []
    for r in json.loads(raw):
        src = canon(r["source"], cfg)
        rid = digest([src, r["text"]])[:24]
        if expected.get(rid) != src:
            raise SystemExit("REPORT_ID_NOT_IN_FROZEN_MANIFEST " + rid)
        rows.append({"report_id": rid, "publisher": src, "url": r["url"],
                     "archive_path": r.get("archive_path", ""), "html_sha256": r.get("html_sha256", ""),
                     "text_sha256": hashlib.sha256(r["text"].encode("utf-8")).hexdigest()})
    if len(rows) != 72 or {r["report_id"] for r in rows} != set(expected):
        raise SystemExit("INCOMPLETE_EXPORT")
    rows.sort(key=lambda r: (r["publisher"], r["report_id"]))
    with a.out.open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    print("wrote", a.out, len(rows), "reports (no text)")


if __name__ == "__main__":
    main()
