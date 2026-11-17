#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
INPUTS="${THREATSCOPE_INPUTS:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/inputs.jsonl}"
MANIFEST="${THREATSCOPE_MANIFEST:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/manifest.json}"
RESULTS="${THREATSCOPE_E2_RESULTS:-$HOME/threat-study/ThreatScope_E2_v0_1_2/results}"
python3 "$ROOT/scripts/analyze_e2.py" --inputs "$INPUTS" --manifest "$MANIFEST" \
  --model Qwen/Qwen2.5-3B-Instruct --results "$RESULTS/E2" --out "$RESULTS/E2_analysis"
