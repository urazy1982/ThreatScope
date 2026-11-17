#!/usr/bin/env bash
# External CPU-only step on Ubuntu-Qua; requires locally available HF tokenizers.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 -m v22core.tokenizer_gate \
  --archive reference/ThreatStudy_v216_Complete_Results.zip \
  --out "${1:-/mnt/g/ThreatStudy/v22_core_tokenizer_gate.json}"
