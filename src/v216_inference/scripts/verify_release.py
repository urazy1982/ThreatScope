from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent.parent
manifest=json.loads((root/'RELEASE_HASHES.json').read_text())
for name,expected in manifest.items():
    f=root/name
    if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=expected:
        raise SystemExit('RELEASE_TAMPERED '+name)
print('RELEASE_INTEGRITY_PASS',len(manifest),'files')
