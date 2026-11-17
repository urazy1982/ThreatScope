"""Export v2.2.1 prediction evidence, without source report texts or model weights."""
from __future__ import annotations
import argparse,zipfile,json,hashlib
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='/mnt/g/ThreatStudy/ThreatStudy_v221_GPU_Results.zip')
    p.add_argument('--logs',default='/mnt/g/ThreatStudy')
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    include=[]
    r=root/'outputs_v221'
    if r.is_dir():include.extend(p for p in r.rglob('*') if p.is_file() and p.suffix!='.part')
    for f in ('RELEASE_HASHES.json','README_v221.md','V221_GPU_READINESS_REPORT.md','protocol/V221_FREEZE_AMENDMENT.md'):
        include.append(root/f)
    logs=Path(args.logs)
    if logs.is_dir():include.extend(p for p in logs.glob('v221_*.log') if p.is_file())
    checksum={}
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(set(include)):
            name=(str(f.relative_to(root)) if f.is_relative_to(root) else 'execution_logs/'+f.name)
            z.write(f,name)
            checksum[name]=hashlib.sha256(f.read_bytes()).hexdigest()
        z.writestr('RESULT_EXPORT_SHA256.json',json.dumps(checksum,indent=2,sort_keys=True)+'\n')
    with zipfile.ZipFile(out) as z:
        bad=z.testzip()
        if bad:raise RuntimeError('EXPORT_CORRUPT_FILE '+bad)
    print('V221_RESULTS_EXPORT',out,'files',len(checksum),'bytes',out.stat().st_size)
    print('Status: archives existing outputs only; does NOT imply all planned GPU calls have completed.')
if __name__=='__main__':main()
