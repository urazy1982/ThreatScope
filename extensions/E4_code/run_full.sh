#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source "$HOME/threat-study/.venv/bin/activate"
mkdir -p /mnt/h/ThreatScope/E4/v0_1/final
python3 scripts/preflight.py
python3 - <<'PY'
import json
from pathlib import Path
from scripts.e4_runner import sha_file,PROTOCOL
p=Path('/mnt/h/ThreatScope/E4/v0_1/smoke_PASS.json')
assert p.is_file(),'SMOKE_NOT_COMPLETE'
r=json.loads(p.read_text())
assert r['status']=='E4_16_RECORD_SMOKE_PASS' and r['protocol']==PROTOCOL and r['runner_sha256']==sha_file('scripts/e4_runner.py'),'STALE_SMOKE_GATE'
print('E4_SMOKE_AUTHORIZATION_PASS')
PY
set -o pipefail
for model in Qwen/Qwen2.5-3B-Instruct meta-llama/Llama-3.2-3B-Instruct; do
 case "$model" in Qwen/*) slug=qwen2.5-3b-instruct;; meta-llama/*) slug=llama-3.2-3b-instruct;;esac
 python3 scripts/e4_runner.py --inputs "$HOME/threat-study/ThreatScope_E3_v0_3/inputs_E3_private.jsonl" --gate /mnt/h/ThreatScope/E3/v0_3/GATE.json --config reference_config.json --model "$model" --precision fp4 --out "results/E4/$slug/fp4" 2>&1 | tee -a /mnt/h/ThreatScope/E4/v0_1/full.log
done
python3 scripts/audit_e4.py --inputs "$HOME/threat-study/ThreatScope_E3_v0_3/inputs_E3_private.jsonl" --gate /mnt/h/ThreatScope/E3/v0_3/GATE.json --config reference_config.json --baseline "$HOME/threat-study/ThreatScope_E3_GPU_v0_4/results/reports/E3_decisions_textfree.csv" --results results/E4 --out results/reports
cp results/reports/* /mnt/h/ThreatScope/E4/v0_1/final/
echo 'E4_1152_CHECKPOINTS_AUDITED_AND_ANALYZED_PASS'
