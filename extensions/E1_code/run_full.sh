#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
INPUTS="${THREATSCOPE_INPUTS:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/inputs.jsonl}"
MANIFEST="${THREATSCOPE_MANIFEST:-$HOME/threat-study/aptcorpus_v214_work/outputs/prepared/manifest.json}"
RESULTS="${THREATSCOPE_RESULTS:-$HOME/threat-study/ThreatScope_v1_1_2/results}"
mkdir -p "$RESULTS/preflight"
python3 "$ROOT/tools/verify_package.py" "$ROOT"
python3 "$ROOT/scripts/prepare_e1_cpu.py" --inputs "$INPUTS" --manifest "$MANIFEST" --out "$RESULTS/preflight/E1_cpu.json"
python3 "$ROOT/scripts/validate_annotation_binding.py" --inputs "$INPUTS" --manifest "$MANIFEST" --labels "$ROOT/reports/C4_exact_288_textfree.csv" --out "$RESULTS/preflight/E1_labels.json"
python3 "$ROOT/scripts/verify_gpu_authorization.py" --mode full --inputs "$INPUTS" --manifest "$MANIFEST" --results "$RESULTS"
python3 "$ROOT/scripts/check_gpu_idle.py"
python3 "$ROOT/scripts/orchestrate_e1.py" --mode full --inputs "$INPUTS" --manifest "$MANIFEST" --results "$RESULTS"
python3 "$ROOT/scripts/audit_e1.py" --mode full --inputs "$INPUTS" --manifest "$MANIFEST" --results "$RESULTS" --out "$RESULTS/preflight/E1_full_audit.json"
python3 "$ROOT/scripts/analyze_e1.py" --inputs "$INPUTS" --manifest "$MANIFEST" --results "$RESULTS" --labels "$ROOT/reports/C4_exact_288_textfree.csv" --out "$RESULTS/analysis"
printf '\nE1_FULL_MATRIX_AUDITED: inspect validity, cardinality, quality and stability together.\n'
