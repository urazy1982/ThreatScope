#!/usr/bin/env bash
set -euo pipefail
RESULTS="${THREATSCOPE_E2_RESULTS:-$HOME/threat-study/ThreatScope_E2_v0_1_2/results}"
DEST="/mnt/h/ThreatScope"
if [ ! -d /mnt/h ]; then echo 'H_DRIVE_NOT_MOUNTED; nothing copied' >&2; exit 2; fi
mkdir -p "$DEST"
for name in E1_review/E1_DIAGNOSTIC_SUMMARY.json E2_analysis/E2_summary.json; do
  if [ -f "$RESULTS/$name" ]; then cp "$RESULTS/$name" "$DEST/$(basename "$name")"; fi
done
printf 'SMALL_REPORTS_COPIED_TO_%s (no checkpoint/embedding sync)\n' "$DEST"
