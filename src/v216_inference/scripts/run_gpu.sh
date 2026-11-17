#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-}"
if [[ -z "$ROOT" || ! -d "$ROOT" ]]; then echo 'USAGE: bash scripts/run_gpu.sh /absolute/staged/workspace'; exit 2; fi
ROOT="$(cd "$ROOT" && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python -m crosscti.gpu_gate --root "$ROOT" --verify-only
python - <<'PYRUN'
from crosscti.analyze import verify_prepared
_,m,ws=verify_prepared('.')
assert m['total_calls']==6912 and len(ws)==144
print('GPU_DATASET_GATE_PASS',m['total_calls'])
PYRUN
while IFS='|' read -r model precision; do
  python -m crosscti.gpu_gate --root "$ROOT" --verify-only >/dev/null
  python -m crosscti.runner --root "$ROOT" --model "$model" --precision "$precision"
done < <(python - <<'PYMODELS'
from crosscti.core import read
cfg=read('config/study.json')
for model in cfg['models']:
  for precision in cfg['precisions']:
    print(model+'|'+precision)
PYMODELS
)
python -m crosscti.analyze --root "$ROOT"
echo 'APT_CROSS_CORPUS_GPU_MATRIX_COMPLETE'
