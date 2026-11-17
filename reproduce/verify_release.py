#!/usr/bin/env python3
"""Verify the SHA-256 of every file listed in SHA256SUMS and the integrity of every zip archive."""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    sums = ROOT / "SHA256SUMS"
    bad, n = [], 0
    for line in sums.read_text().splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(maxsplit=1)
        rel = rel.lstrip("*")
        p = ROOT / rel
        n += 1
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            bad.append(rel)
        elif p.suffix == ".zip":
            with zipfile.ZipFile(p) as z:
                if z.testzip() is not None:
                    bad.append(rel + " (corrupt zip)")
    if bad:
        print("FAILED:", *bad, sep="\n  ")
        sys.exit(1)
    print(f"RELEASE_VERIFIED {n} files")


if __name__ == "__main__":
    main()
