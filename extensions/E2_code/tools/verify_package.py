#!/usr/bin/env python3
"""Strict SHA-256 verification of immutable ThreatScope E2 software package."""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
manifest=json.loads((root/'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
for name,expected in sorted(manifest['files'].items()):
    p=root/name
    if not p.is_file():raise SystemExit('E2_PACKAGE_FILE_MISSING '+name)
    observed=hashlib.sha256(p.read_bytes()).hexdigest()
    if observed!=expected:raise SystemExit('E2_PACKAGE_FILE_DRIFT '+name)
print('THREATSCOPE_E2_PACKAGE_INTEGRITY_PASS',len(manifest['files']),'files')
