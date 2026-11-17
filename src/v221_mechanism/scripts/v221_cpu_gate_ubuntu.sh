#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 scripts/verify_release.py
python3 -m unittest discover -s tests -q
mkdir -p /mnt/g/ThreatStudy
GATE="/mnt/g/ThreatStudy/v221_real_tokenizer_gate.json"
python3 -m v22core.tokenizer_gate \
  --archive reference/ThreatStudy_v216_Complete_Results.zip --out "$GATE"
python3 -m v22core.gpu_handoff authorize --root "$ROOT" --tokenizer-gate "$GATE"
echo V221_CPU_AUTHORIZATION_PASS
