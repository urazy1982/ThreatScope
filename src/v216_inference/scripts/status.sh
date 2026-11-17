#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
python - <<'PY'
from crosscti.core import read,cell_id
from pathlib import Path
cfg=read('config/study.json');mf=Path('outputs/prepared/manifest.json')
if not mf.exists():print('DATASET_NOT_PREPARED');raise SystemExit
m=read(mf);all_done=0
for model in cfg['models']:
 for precision in cfg['precisions']:
  d=Path('outputs/runs')/cell_id(model,precision)
  counts=[len(list((d/f'example_{k}').glob('*.json'))) for k in range(8)]
  all_done+=sum(counts)
  print(model,precision,sum(counts),'/',len(counts)*m['windows'],'by_anchor',counts,'metadata',(d/'run_metadata.json').exists())
print('OVERALL',all_done,'/',m['total_calls'])
PY
