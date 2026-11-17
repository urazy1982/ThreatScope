#!/usr/bin/env bash
set -euo pipefail
ARM="${1:-}"
if [[ "$ARM" != "C" && "$ARM" != "B" ]]; then echo 'USAGE: bash scripts/v221_run_arm_gpu.sh C|B' >&2; exit 2; fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 -m v22core.gpu_handoff verify --root "$ROOT"
python3 -m v22core.gpu_handoff status --root "$ROOT" > /dev/null
# Require 432 archived-env comparison records before changing inference arms.
python3 - <<'PY'
import json,pathlib,zipfile
base=pathlib.Path('outputs_v221/runs/replay')
files=list(base.glob('*/**/example_*/*.json'))
if len(files)!=432:raise SystemExit('REPLAY_NOT_COMPLETE_EXPECTED_432_GOT_'+str(len(files)))
PY
while IFS='|' read -r model precision; do
  python3 -m v22core.gpu_handoff run --root "$ROOT" --arm "$ARM" --model "$model" --precision "$precision"
done < <(python3 - <<'PY'
import json,zipfile
with zipfile.ZipFile('reference/ThreatStudy_v216_Complete_Results.zip') as z:
 cfg=json.loads(z.read('config/study.json'))
for model in cfg['models']:
 for precision in cfg['precisions']: print(model+'|'+precision)
PY
)
python3 -m v22core.gpu_handoff status --root "$ROOT"
echo "V221_GPU_ARM_${ARM}_6912_COMPLETE"
