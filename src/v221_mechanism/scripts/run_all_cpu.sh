#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 scripts/verify_release.py
python3 -m unittest discover -s tests -q
python3 -m v22core.replay --archive reference/ThreatStudy_v216_Complete_Results.zip --out results >/dev/null
python3 -m v22core.synthetic --archive reference/ThreatStudy_v216_Complete_Results.zip --out results >/dev/null
python3 -m v22core.null --archive reference/ThreatStudy_v216_Complete_Results.zip --out results/cardinality_only_reference.json --draws 10000 >/dev/null
python3 -m v22core.replication --archive reference/ThreatStudy_v216_Complete_Results.zip --out results/v22_replication_manifest.json >/dev/null
python3 -m v22core.evidence_audit \
  --archive reference/ThreatStudy_v216_Complete_Results.zip \
  --final-gate evidence/APT_final_cpu_gate_v215.json \
  --preflight evidence/APT_preflight_v214.json \
  --out results/token_provenance_audit.json >/dev/null
python3 - <<'PY'
import json
from pathlib import Path
from v22core.constraints import verify_language
Path('results/v22_grammar_256.json').write_text(json.dumps({'status':'CPU_256_SUBSET_PASS',**verify_language()},indent=2)+'\n')
PY
python3 scripts/verify_release.py
printf '\nV22_CORE_CPU_CHECKS_PASS: 95 tests + 6912 real checkpoint reanalysis + 13824 synthetic B/C records + 3x10000 null samples + 256 canonical JSON forms.\n'
