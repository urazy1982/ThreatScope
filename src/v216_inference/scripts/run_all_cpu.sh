#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
python3 scripts/verify_release.py
python3 -m unittest discover -s tests -v
python3 scripts/cpu_replay.py --root .
python3 scripts/evidence_audit.py \
  --ctinexus-audit evidence/CTINexus_provenance_audit.json \
  --v151-zip evidence/ThreatStudy_v151_Analysis_Results.zip \
  --output outputs/cpu_validation/real_evidence_results.json
python3 scripts/source_power_simulation.py --output outputs/cpu_validation/source_power_simulation.json
python3 -m compileall -q crosscti scripts tests
bash -n scripts/run_gpu.sh
if bash scripts/run_gpu.sh >/tmp/threat_v202_gpu_gate.log 2>&1; then
  echo GPU_GATE_UNEXPECTEDLY_OPEN
  exit 25
else
  if ! grep -q GPU_PROVENANCE_GATE_CLOSED /tmp/threat_v202_gpu_gate.log; then
    cat /tmp/threat_v202_gpu_gate.log
    exit 26
  fi
fi
printf 'ALL_AVAILABLE_CPU_CHECKS_PASS\n'
