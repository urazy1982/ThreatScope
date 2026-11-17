#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
INPUTS="${THREATSCOPE_INPUTS:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/inputs.jsonl}"
RESULTS="${THREATSCOPE_RESULTS:-$HOME/threat-study/ThreatScope_v1_1_2/results}"
mkdir -p "$ROOT/source_release" "$RESULTS/preflight"
if [[ ! -e "$ROOT/source_release/ThreatScope/data/config/study.json" ]]; then
  unzip -q "$ROOT/upstream/ThreatScope_v1.0.0.zip" -d "$ROOT/source_release"
fi
python3 "$ROOT/scripts/c8_prompt_gate.py" \
 --release "$ROOT/source_release/ThreatScope" --inputs "$INPUTS" \
 --out "$RESULTS/preflight/C8_actual_tokenizer_ids.json" --tokenizer-id-check
printf '\nC8_TOKENIZER_COMPARISON_COMPLETED. Inspect observed token distances; one-token change is NOT assumed.\n'
