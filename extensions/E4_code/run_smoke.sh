#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source "$HOME/threat-study/.venv/bin/activate"
mkdir -p /mnt/h/ThreatScope/E4/v0_1 results/preflight
python3 scripts/preflight.py
set -o pipefail
python3 scripts/e4_runner.py \
 --inputs "$HOME/threat-study/ThreatScope_E3_v0_3/inputs_E3_private.jsonl" \
 --gate /mnt/h/ThreatScope/E3/v0_3/GATE.json \
 --config reference_config.json \
 --model Qwen/Qwen2.5-3B-Instruct --precision fp4 --limit 2 \
 --out results/E4/qwen2.5-3b-instruct/fp4 \
 2>&1 | tee /mnt/h/ThreatScope/E4/v0_1/smoke.log
python3 - <<'PY'
from pathlib import Path
from scripts.e4_runner import load_frozen,validate_checkpoint,sha_file,PROTOCOL
from vendor.core import read,digest
base=Path('results/E4/qwen2.5-3b-instruct/fp4'); meta=read(base/'run_metadata.json')
assert meta['protocol']==PROTOCOL
assert meta['runner_sha256']==sha_file('scripts/e4_runner.py')
ws,gate,cfg=load_frozen(Path.home()/'threat-study/ThreatScope_E3_v0_3/inputs_E3_private.jsonl',Path('/mnt/h/ThreatScope/E3/v0_3/GATE.json'),Path('reference_config.json'))
for w in ws[:2]:
 for k in range(8):
  p=base/f'example_{k}'/(w['window_id']+'.json')
  assert p.is_file(),str(p)
  validate_checkpoint(p,w,k,meta['model'],'fp4',meta['revision'],digest(meta))
Path('/mnt/h/ThreatScope/E4/v0_1/smoke_PASS.json').write_text('{"status":"E4_16_RECORD_SMOKE_PASS","protocol":"'+PROTOCOL+'","runner_sha256":"'+sha_file('scripts/e4_runner.py')+'"}\n')
print('E4_16_RECORD_SMOKE_AUDIT_PASS')
PY
