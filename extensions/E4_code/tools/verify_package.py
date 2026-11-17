from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'SHA256_MANIFEST.json').read_text())
for rel,expected in manifest.items():
 p=root/rel
 assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==expected, 'PACKAGE_INTEGRITY_FAIL '+rel
print('THREATSCOPE_E4_PACKAGE_INTEGRITY_PASS',len(manifest),'files')
