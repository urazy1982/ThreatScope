#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
INPUT="$HOME/threat-study/ThreatScope_E3_v0_3/inputs_E3_private.jsonl"
GATE=/mnt/h/ThreatScope/E3/v0_3/GATE.json
mkdir -p /mnt/h/ThreatScope/E3/v0_4
python3 -m unittest discover -s tests -v 2>&1 | tee /mnt/h/ThreatScope/E3/v0_4/cpu_tests.log
python3 scripts/e3_runner.py --inputs "$INPUT" --gate "$GATE" --config reference_config.json --model Qwen/Qwen2.5-3B-Instruct --precision bf16 --out results/E3/qwen2.5-3b-instruct/bf16 --check-only 2>&1 | tee /mnt/h/ThreatScope/E3/v0_4/preflight.log
