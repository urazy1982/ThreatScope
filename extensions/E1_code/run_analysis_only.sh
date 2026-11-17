#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
INPUTS="${THREATSCOPE_INPUTS:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/inputs.jsonl}"
MANIFEST="${THREATSCOPE_MANIFEST:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/manifest.json}"
RESULTS="${THREATSCOPE_RESULTS:-$HOME/threat-study/ThreatScope_v1_1_2/results}"
python3 "$ROOT/scripts/audit_e1.py" --mode full --inputs "$INPUTS" --manifest "$MANIFEST" \
 --results "$RESULTS" --out "$RESULTS/preflight/E1_full_audit.json"
python3 "$ROOT/scripts/analyze_e1.py" --inputs "$INPUTS" --manifest "$MANIFEST" \
 --results "$RESULTS" --labels "$ROOT/reports/C4_exact_288_textfree.csv" --out "$RESULTS/analysis"
