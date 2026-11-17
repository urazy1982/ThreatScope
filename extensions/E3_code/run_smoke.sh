#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source "$HOME/threat-study/.venv/bin/activate"
mkdir -p /mnt/h/ThreatScope/E3/v0_4
set -o pipefail
python3 scripts/e3_runner.py --inputs "$HOME/threat-study/ThreatScope_E3_v0_3/inputs_E3_private.jsonl" --gate /mnt/h/ThreatScope/E3/v0_3/GATE.json --config reference_config.json --model Qwen/Qwen2.5-3B-Instruct --precision bf16 --out results/E3/qwen2.5-3b-instruct/bf16 --limit 2 2>&1 | tee /mnt/h/ThreatScope/E3/v0_4/smoke.log
python3 scripts/audit_e3.py --inputs "$HOME/threat-study/ThreatScope_E3_v0_3/inputs_E3_private.jsonl" --gate /mnt/h/ThreatScope/E3/v0_3/GATE.json --config reference_config.json --results results/E3 --out results/reports --allow-partial
cp results/reports/E3_audit.json /mnt/h/ThreatScope/E3/v0_4/smoke_audit.json
