#!/usr/bin/env python3
"""Verify the entire ThreatScope release against release/SHA256_MANIFEST.json."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parent
manifest=json.loads((root/'release/SHA256_MANIFEST.json').read_text(encoding='utf8'))
expected=manifest['files']
for rel,sha in expected.items():
 p=root/rel
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:
  raise SystemExit('THREATSCOPE_RELEASE_HASH_FAIL: '+rel)
actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix()!='release/SHA256_MANIFEST.json'}
if actual!=set(expected):
 raise SystemExit(f'THREATSCOPE_RELEASE_FILE_SET_FAIL missing={sorted(set(expected)-actual)[:10]} extra={sorted(actual-set(expected))[:10]}')
print('THREATSCOPE_RELEASE_SHA256_PASS',len(expected),'files')
