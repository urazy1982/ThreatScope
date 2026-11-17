#!/usr/bin/env python3
"""SHA-256 integrity check for all immutable handoff files."""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
manifest=json.loads((root/'SHA256_MANIFEST.json').read_text())
for rel,expected in manifest['files'].items():
 path=root/rel
 if not path.is_file():raise SystemExit('MISSING_PACKAGE_FILE '+rel)
 actual=hashlib.sha256(path.read_bytes()).hexdigest()
 if actual!=expected:raise SystemExit('PACKAGE_INTEGRITY_FAIL '+rel)
print('THREATSCOPE_E1_GPU_HANDOFF_INTEGRITY_PASS',len(manifest['files']),'files')
