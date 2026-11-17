#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
INPUTS="${THREATSCOPE_INPUTS:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/inputs.jsonl}"
MANIFEST="${THREATSCOPE_MANIFEST:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/manifest.json}"
python3 "$ROOT/tools/verify_package.py" "$ROOT"
PYTHONPATH="$ROOT" python3 -m unittest discover -s "$ROOT/tests" -q
for model in Qwen/Qwen2.5-3B-Instruct meta-llama/Llama-3.2-3B-Instruct mistralai/Mistral-7B-Instruct-v0.3; do
  for precision in bf16 nf4; do
    PYTHONPATH="$ROOT" python3 "$ROOT/scripts/e2_singleton_gpu.py" \
      --inputs "$INPUTS" --manifest "$MANIFEST" --model "$model" \
      --precision "$precision" --out "$ROOT/results/_preflight_unused" --preflight-only
  done
done
printf 'THREATSCOPE_E2_ALL_CPU_GATES_PASS (GPU not used)\n'
