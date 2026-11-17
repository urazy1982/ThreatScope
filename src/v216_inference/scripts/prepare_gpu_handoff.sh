#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="${1:-}"
SMAH="${2:-}"
if [[ -z "$WORKSPACE" || -z "$SMAH" ]]; then echo 'USAGE: bash scripts/prepare_gpu_handoff.sh /absolute/staged/workspace /absolute/smah/inputs.jsonl'; exit 2; fi
cd "$(dirname "${BASH_SOURCE[0]}")/.."
RELEASE="$PWD"
python scripts/verify_release.py
[[ -d "$WORKSPACE/crosscti" && -f "$WORKSPACE/outputs/prepared/manifest.json" ]] || { echo 'STAGED_WORKSPACE_MISSING'; exit 3; }
[[ -f "$SMAH" ]] || { echo 'SMAH_BASELINE_MISSING'; exit 4; }
WORKSPACE="$(cd "$WORKSPACE" && pwd)"
# Never overwrite existing inference records with a changed source protocol.
if [[ -d "$WORKSPACE/outputs/runs" ]] && [[ -n "$(find "$WORKSPACE/outputs/runs" -type f -print -quit)" ]]; then
  echo 'GPU_OUTPUT_ALREADY_PRESENT_REVIEW_BEFORE_CODE_UPDATE'; exit 5
fi
mkdir -p "$WORKSPACE/corpusapt" "$WORKSPACE/crosscti"
cp "$RELEASE/corpusapt/acquire.py" "$WORKSPACE/corpusapt/acquire.py"
cp "$RELEASE/corpusapt/__init__.py" "$WORKSPACE/corpusapt/__init__.py"
for f in core.py prepare.py analyze.py runner.py token_encoding.py preflight.py final_cpu_gate.py gpu_gate.py; do
  cp "$RELEASE/crosscti/$f" "$WORKSPACE/crosscti/$f"
done
export PYTHONPATH="$WORKSPACE${PYTHONPATH:+:$PYTHONPATH}"
python -m crosscti.gpu_gate --root "$WORKSPACE" --smah-inputs "$SMAH"
echo 'DATASET_BOUND_GPU_HANDOFF_READY'
