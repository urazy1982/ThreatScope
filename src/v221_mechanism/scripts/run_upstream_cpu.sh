#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT
unzip -q "$ROOT/reference/ThreatStudy_APT_Corpus_v2_1_6_GPU_Handoff.zip" -d "$TEMP"
cd "$TEMP/ThreatStudy_APT_Corpus_v2_1_6_GPU_Handoff"
PYTHONPATH="$PWD" python3 -m unittest discover -s tests -q
printf 'V216_ORIGINAL_94_TESTS_PASS\n'
