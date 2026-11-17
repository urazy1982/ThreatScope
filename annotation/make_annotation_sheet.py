#!/usr/bin/env python3
"""Create blinded annotation workbooks from a local copy of the original inputs.jsonl.

The original inputs contain report text and are NOT distributed with this
repository. The file is verified against the frozen input hash before use.
Model outputs are never read, so the sheets are blind to model decisions.

    python3 annotation/make_annotation_sheet.py --inputs /path/to/inputs.jsonl \
        --annotators A B --out annotation/private_sheets

Requires openpyxl for .xlsx output; falls back to CSV otherwise.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
COLUMNS = ["item_id", "window", "idx", "context_before", "TARGET_sentence",
           "relevant", "unsure", "note"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", type=Path, required=True)
    ap.add_argument("--annotators", nargs="+", default=["A", "B"])
    ap.add_argument("--out", type=Path, default=HERE / "private_sheets")
    a = ap.parse_args()

    raw = a.inputs.read_bytes()
    frozen = json.loads((ROOT / "data/prepared/manifest.json").read_text())["input_sha256"]
    if hashlib.sha256(raw).hexdigest() != frozen:
        raise SystemExit("INPUT_HASH_MISMATCH: not the frozen v2.1.6 inputs.jsonl")
    windows = {w["window_id"]: w for w in map(json.loads, filter(str.strip, raw.decode("utf-8").splitlines()))}

    items = list(csv.DictReader((HERE / "subset_items.csv").open()))
    rows = []
    for it in items:
        s = windows[it["window_id"]]["sentences"][int(it["sentence_index"])]
        if s["uid"] != it["sentence_uid"] or hashlib.sha256(s["sentence_text"].encode()).hexdigest() != it["sentence_sha256"]:
            raise SystemExit("SUBSET_IDENTITY_MISMATCH " + it["item_id"])
        rows.append([it["item_id"], int(it["presentation_order"]), int(it["sentence_index"]),
                     s["context_before"] or "", s["sentence_text"], "", "", ""])

    a.out.mkdir(parents=True, exist_ok=True)
    guide = (HERE / "GUIDELINES.md").read_text()
    try:
        import openpyxl
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.worksheet.datavalidation import DataValidation
    except ImportError:
        openpyxl = None
    for ann in a.annotators:
        if openpyxl is None:
            p = a.out / f"annotation_sheet_{ann}.csv"
            with p.open("w", newline="", encoding="utf-8") as f:
                wr = csv.writer(f)
                wr.writerow(COLUMNS)
                wr.writerows(rows)
            print("wrote", p)
            continue
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "label_here"
        ws.append(COLUMNS)
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="1F3A5F")
        shade = PatternFill("solid", fgColor="F2F5F9")
        answer = PatternFill("solid", fgColor="FFF4D6")
        for r in rows:
            ws.append(r)
            if r[1] % 2 == 0:
                for c in ws[ws.max_row][:5]:
                    c.fill = shade
            for c in ws[ws.max_row][5:]:
                c.fill = answer
        widths = {"A": 10, "B": 8, "C": 6, "D": 40, "E": 95, "F": 10, "G": 8, "H": 30}
        for col, wdt in widths.items():
            ws.column_dimensions[col].width = wdt
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "F2"
        dv = DataValidation(type="list", formula1='"1,0"', allow_blank=True)
        dv.error, dv.errorTitle = "Enter 1 (relevant) or 0 (not relevant)", "Invalid label"
        ws.add_data_validation(dv)
        dv.add(f"F2:F{len(rows)+1}")
        dv2 = DataValidation(type="list", formula1='"Y"', allow_blank=True)
        ws.add_data_validation(dv2)
        dv2.add(f"G2:G{len(rows)+1}")
        g = wb.create_sheet("guidelines")
        g.column_dimensions["A"].width = 120
        for line in guide.splitlines():
            g.append([line])
            g[g.max_row][0].alignment = Alignment(wrap_text=True)
        wb.active = 0
        p = a.out / f"annotation_sheet_{ann}.xlsx"
        wb.save(p)
        print("wrote", p, len(rows), "items")


if __name__ == "__main__":
    main()
