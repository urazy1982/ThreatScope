#!/usr/bin/env python3
"""Verify the SHA-256 of every file listed in SHA256SUMS (v1.0.0) or release/SHA256_MANIFEST.json (v1.1.0)
and the integrity of every zip archive."""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    sums = ROOT / "SHA256SUMS"
    if sums.is_file():  # v1.0.0 layout
        entries = []
        for line in sums.read_text().splitlines():
            if line.strip():
                digest, rel = line.split(maxsplit=1)
                entries.append((digest, rel.lstrip("*")))
    else:  # v1.1.0 layout: one manifest for the whole release
        import json
        manifest = json.loads((ROOT / "release" / "SHA256_MANIFEST.json").read_text(encoding="utf8"))
        entries = [(digest, rel) for rel, digest in manifest["files"].items()]
    bad, n = [], 0
    for digest, rel in entries:
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
