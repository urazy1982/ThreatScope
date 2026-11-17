#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 -m v22core.gpu_handoff verify --root "$ROOT"
while IFS='|' read -r model precision; do
  python3 -m v22core.gpu_handoff run --root "$ROOT" --arm replay --model "$model" --precision "$precision"
done < <(python3 - <<'PY'
import json,zipfile
with zipfile.ZipFile('reference/ThreatStudy_v216_Complete_Results.zip') as z:
 cfg=json.loads(z.read('config/study.json'))
for model in cfg['models']:
 for precision in cfg['precisions']: print(model+'|'+precision)
PY
)
python3 -m v22core.gpu_handoff status --root "$ROOT"
echo V221_REPLAY_GPU_432_COMPLETE
