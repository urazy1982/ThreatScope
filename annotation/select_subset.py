#!/usr/bin/env python3
"""Pre-declared, outcome-blind selection of the human-annotation subset.

Selection uses only window/report identifiers and a fixed salt; it never reads
model outputs. Design: 9 publishers x 4 reports x 1 window = 36 windows,
36 x 8 = 288 target sentences.

    python3 annotation/select_subset.py      # writes subset_windows.csv, subset_items.csv
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SALT = "ThreatStudy-v2.3-human-annotation-subset-2026-11-13"
REPORTS_PER_PUBLISHER = 4


def h(*parts: str) -> str:
    return hashlib.sha256("|".join((SALT,) + parts).encode("utf-8")).hexdigest()


def main() -> None:
    windows = [json.loads(l) for l in (ROOT / "data/prepared/inputs_redacted.jsonl").read_text().splitlines() if l.strip()]
    by_pub = defaultdict(lambda: defaultdict(list))
    for w in windows:
        by_pub[w["source"]][w["report_id"]].append(w)
    chosen = []
    for pub in sorted(by_pub):
        reports = sorted(by_pub[pub], key=lambda r: h(pub, r))[:REPORTS_PER_PUBLISHER]
        for r in reports:
            ws = sorted(by_pub[pub][r], key=lambda w: w["window_slot"])
            slot = int(h(pub, r, "slot"), 16) % len(ws)
            chosen.append(ws[slot])
    assert len(chosen) == 9 * REPORTS_PER_PUBLISHER
    # Presentation order: shuffled across publishers so annotators do not label publisher blocks.
    chosen.sort(key=lambda w: h("order", w["window_id"]))
    with (HERE / "subset_windows.csv").open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["presentation_order", "window_id", "report_id", "publisher", "window_slot"])
        for n, w in enumerate(chosen, 1):
            wr.writerow([n, w["window_id"], w["report_id"], w["source"], w["window_slot"]])
    with (HERE / "subset_items.csv").open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["item_id", "presentation_order", "window_id", "sentence_index", "sentence_uid", "sentence_sha256"])
        for n, w in enumerate(chosen, 1):
            for s in w["sentences"]:
                wr.writerow([f"W{n:02d}-S{s['i']}", n, w["window_id"], s["i"], s["uid"], s["sentence_sha256"]])
    print(f"selected {len(chosen)} windows / {8*len(chosen)} sentences; salt={SALT}")


if __name__ == "__main__":
    main()
