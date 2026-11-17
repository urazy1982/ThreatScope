#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
INPUTS="${THREATSCOPE_INPUTS:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/inputs.jsonl}"
MANIFEST="${THREATSCOPE_MANIFEST:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/manifest.json}"
E1_ROOT="${THREATSCOPE_E1_RESULTS:-$HOME/threat-study/ThreatScope_v1_1_2/results}"
LABELS="${THREATSCOPE_E1_LABELS:-$HOME/threat-study/ThreatScope_v1_1_2/reports/C4_exact_288_textfree.csv}"
RESULTS="${THREATSCOPE_E2_RESULTS:-$HOME/threat-study/ThreatScope_E2_v0_1_2/results}"
python3 "$ROOT/scripts/e1_invalid_and_matched_quality.py" \
  --inputs "$INPUTS" --manifest "$MANIFEST" --results "$E1_ROOT" --labels "$LABELS" \
  --out "$RESULTS/E1_review"
printf 'THREATSCOPE_E1_FORMAT_AND_MATCHED_F1_CPU_REANALYSIS_PASS\n'
