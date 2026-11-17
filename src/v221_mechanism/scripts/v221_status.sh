#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT";export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 -m v22core.gpu_handoff status --root "$ROOT"
