# ThreatScope E2 v0.1.2 — Chat input tensor normalization

## Observed failure

After the historical suffix gate passed, v0.1.1 raised `BAD_CHAT_INPUT_TENSOR` at the initial chat encoding step. This was caused by expecting a 2D torch.Tensor while `apply_chat_template` in the deployed transformers stack returned an accepted flat list or mapping. No E2 GPU predictions were reported.

## Repair

`normalize_chat_input` calls the unchanged frozen historical `extract_ids` helper and builds `torch.tensor([ids], dtype=torch.long)`. It explicitly rejects malformed, empty, and batched outputs. It does not change the prompt text, token sequence, candidate space, EOT, quantization, decoding, or frozen Arm C scoring. The protocol and checkpoint identity are versioned to v0.1.2 because the runner source changed.

## Launch

Download the ZIP to `C:\Users\uraz\Downloads`, extract to `~/threat-study/ThreatScope_E2_v0_1_2`, activate `~/threat-study/.venv`, run `bash run_preflight.sh` then `bash run_smoke.sh`. The Windows diagnostic log is `/mnt/h/ThreatScope/E2/E2_v011_smoke_audit.log`; preserve it with the original filename if produced but use v0.1.2 logs for this run.

Do not reuse v0.1.1 checkpoints. This package does not claim GPU inference has passed.
