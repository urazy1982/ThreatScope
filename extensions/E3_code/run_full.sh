#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source "$HOME/threat-study/.venv/bin/activate"
mkdir -p /mnt/h/ThreatScope/E3/v0_4
if [[ ! -f /mnt/h/ThreatScope/E3/v0_4/smoke_audit.json ]]; then echo 'BLOCKED: Run run_smoke.sh first';exit 2;fi
python3 - <<'PY'
import json
r=json.load(open('/mnt/h/ThreatScope/E3/v0_4/smoke_audit.json'))
assert r['total']==16 and r['cells'][0]['total']==16, 'SMOKE_INCOMPLETE'
print('SMOKE_AUTHORIZATION_PASS')
PY
set -o pipefail
for model in 'Qwen/Qwen2.5-3B-Instruct' 'meta-llama/Llama-3.2-3B-Instruct' 'mistralai/Mistral-7B-Instruct-v0.3';do
 for precision in bf16 nf4;do
  case "$model" in Qwen/*) slug='qwen2.5-3b-instruct';; meta-llama/*)slug='llama-3.2-3b-instruct';; mistralai/*)slug='mistral-7b-instruct-v0-3';;esac
  python3 scripts/e3_runner.py --inputs "$HOME/threat-study/ThreatScope_E3_v0_3/inputs_E3_private.jsonl" --gate /mnt/h/ThreatScope/E3/v0_3/GATE.json --config reference_config.json --model "$model" --precision "$precision" --out "results/E3/$slug/$precision" 2>&1 | tee -a /mnt/h/ThreatScope/E3/v0_4/full.log
 done
done
python3 scripts/audit_e3.py --inputs "$HOME/threat-study/ThreatScope_E3_v0_3/inputs_E3_private.jsonl" --gate /mnt/h/ThreatScope/E3/v0_3/GATE.json --config reference_config.json --results results/E3 --out results/reports
mkdir -p /mnt/h/ThreatScope/E3/v0_4/final
cp results/reports/* /mnt/h/ThreatScope/E3/v0_4/final/
echo E3_3456_CHECKPOINT_AUDIT_AND_ANALYSIS_PASS
