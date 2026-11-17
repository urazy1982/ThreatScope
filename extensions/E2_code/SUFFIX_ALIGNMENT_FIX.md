# ThreatScope E2 v0.1.1 suffix alignment correction

User-supplied CPU diagnostic: `status=MATCH`, `prefix_identical=true`, `matches_plus_newline=true`. Qwen assistant turn serializer adds a newline token after `<|im_end|>`. The historical scored candidate includes `<|im_end|>` but excludes the trailing newline.

The runner now uses the **same `extract_ids` and `continuation_matches_full` functions** already present in the immutable historical tokenizer gate. It accepts only exact scored candidate or that exact candidate followed by exactly the tokenizer-encoded newline. It fails closed on any other suffix, and does not modify scored candidate IDs, model prompting, decoding or quantization settings.

The protocol/checkpoint identity changed to `v0.1.1` due to runner source change; do not reuse `v0.1.0` checkpoints. The earlier smoke failed before model inference and generated no valid results. If output directories contain earlier checkpoints, stop and archive them separately before running.

This package is CPU-tested only. Real Qwen smoke inference remains to be executed locally, with the existing frozen stack and no competing GPU processes.

Install: download ZIP to `C:\Users\uraz\Downloads`; extract to new `~/threat-study/ThreatScope_E2_v0_1_1`; source `~/threat-study/.venv/bin/activate`; run `bash run_preflight.sh` followed by `bash run_smoke.sh`. Export reports to Windows `H:\ThreatScope\E2` after smoke, without copying restricted data automatically.
