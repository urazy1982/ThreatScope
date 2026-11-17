# ThreatScope E4 v0.1.1 — Preflight configuration correction

The original `reference_config.json` supplied `e4_protocol='ThreatScope-E4-FP4-v0.1-retrospective-same-bit-width'` whereas `scripts/e4_runner.py` required `ThreatScope-E4-FP4-v0.1-historical-ArmA-interior-report-holdout`. This caused `DECODE_CONFIG_DRIFT` before GPU inference. The revised JSON now matches the original runner constant; max_new_tokens=96 and max_input_tokens=8192 are unchanged.

No inference logic, model revisions, prompt definitions, quantization settings, dataset hashes, or historical checkpoint contents changed. This is a packaging configuration correction.

The SHA-256 manifest was regenerated for the corrected package; run `python3 tools/verify_package.py` and `bash run_preflight.sh`. Keep existing GPU output untouched; do not combine checkpoints from different runner identities unless a full provenance check permits it.
