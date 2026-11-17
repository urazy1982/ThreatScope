#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
INPUTS="${THREATSCOPE_INPUTS:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/inputs.jsonl}"
MANIFEST="${THREATSCOPE_MANIFEST:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/manifest.json}"
RESULTS="${THREATSCOPE_E2_RESULTS:-$HOME/threat-study/ThreatScope_E2_v0_1_2/results}"
MODEL=Qwen/Qwen2.5-3B-Instruct
python3 "$ROOT/tools/verify_package.py" "$ROOT"
python3 "$ROOT/scripts/audit_e2.py" --inputs "$INPUTS" --manifest "$MANIFEST" \
  --model "$MODEL" --precision bf16 --out "$RESULTS/E2/qwen2.5-3b/bf16" --limit 2
for precision in bf16 nf4; do
   python3 "$ROOT/scripts/check_gpu_idle.py"
   OUT="$RESULTS/E2/qwen2.5-3b/$precision"
   python3 "$ROOT/scripts/e2_singleton_gpu.py" --inputs "$INPUTS" --manifest "$MANIFEST" \
     --model "$MODEL" --precision "$precision" --out "$OUT"
   python3 "$ROOT/scripts/audit_e2.py" --inputs "$INPUTS" --manifest "$MANIFEST" \
     --model "$MODEL" --precision "$precision" --out "$OUT"
done
python3 "$ROOT/scripts/analyze_e2.py" --inputs "$INPUTS" --manifest "$MANIFEST" \
  --model "$MODEL" --results "$RESULTS/E2" --out "$RESULTS/E2_analysis"
printf 'THREATSCOPE_E2_QWEN_2304_GENERATIONS_AUDITED_AND_ANALYZED_PASS\n'
