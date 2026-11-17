#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
INPUTS="${THREATSCOPE_INPUTS:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/inputs.jsonl}"
MANIFEST="${THREATSCOPE_MANIFEST:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/manifest.json}"
RESULTS="${THREATSCOPE_E2_RESULTS:-$HOME/threat-study/ThreatScope_E2_v0_1_2/results}"
MODEL=Qwen/Qwen2.5-3B-Instruct
OUT="$RESULTS/E2/qwen2.5-3b/bf16"
python3 "$ROOT/tools/verify_package.py" "$ROOT"
python3 "$ROOT/scripts/e2_singleton_gpu.py" --inputs "$INPUTS" --manifest "$MANIFEST" \
  --model "$MODEL" --precision bf16 --out "$OUT" --limit 2 --preflight-only
python3 - <<'PY'
import sys,torch,transformers,bitsandbytes
print('E2_PYTHON',sys.executable,'torch',torch.__version__,'transformers',transformers.__version__,'bnb',bitsandbytes.__version__)
assert torch.cuda.is_available()
assert torch.__version__=='2.10.0+cu128'
assert transformers.__version__=='5.22.2'
assert bitsandbytes.__version__=='0.50.2'
PY
python3 "$ROOT/scripts/check_gpu_idle.py"
python3 "$ROOT/scripts/e2_singleton_gpu.py" --inputs "$INPUTS" --manifest "$MANIFEST" \
  --model "$MODEL" --precision bf16 --out "$OUT" --limit 2
python3 "$ROOT/scripts/audit_e2.py" --inputs "$INPUTS" --manifest "$MANIFEST" \
  --model "$MODEL" --precision bf16 --out "$OUT" --limit 2
printf 'THREATSCOPE_E2_TWO_WINDOW_SMOKE_PASS (16 actual constrained generations)\n'

# Export only small diagnostic reports to Windows (never raw report text).
WIN_E2="${THREATSCOPE_WINDOWS_E2:-/mnt/h/ThreatScope/E2}"
if [ -d /mnt/h ]; then
  mkdir -p "$WIN_E2"
  python3 "$ROOT/scripts/audit_e2.py" --inputs "$INPUTS" --manifest "$MANIFEST" \
    --model "$MODEL" --precision bf16 --out "$OUT" --limit 2 \
    > "$WIN_E2/E2_v012_smoke_audit.log" 2>&1
  printf 'E2_SMOKE_WINDOWS_AUDIT_WRITTEN %s\n' "$WIN_E2/E2_v012_smoke_audit.log"
else
  printf 'WINDOWS_COPY_BLOCKED /mnt/h not mounted; audit remains in Ubuntu\n'
fi
