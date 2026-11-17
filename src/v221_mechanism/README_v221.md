# ThreatStudy v2.2.1 — Corrected tokenizer gate and guarded GPU handoff

**Working title:** One Digit, Different Decisions: Quantization-Dependent Example Sensitivity in Structured Cyber-Threat Intelligence Relevance Selection.

**Local CPU validation:** executable tests and immutable archive replay. **No new real model inferences were carried out on this server.** This package preserves the previous full v2.2-Core release, fixes a chat-template alignment bug, and introduces an experimental GPU launcher. A real Hugging Face tokenizer rerun in **Ubuntu-Qua** is required before use.

## Extract

Copy `ThreatStudy_v221_GPU_Readiness.zip` to Windows `G:\\ThreatStudy`, then on Ubuntu-Qua:

```bash
cd ~/threat-study
unzip -o /mnt/g/ThreatStudy/ThreatStudy_v221_GPU_Readiness.zip -d ~/threat-study
source ~/threat-study/.venv/bin/activate
cd ~/threat-study/ThreatStudy_v221_GPU_Readiness
```

## Gate 0: real CPU tokenizer, revision and dataset authorization

```bash
bash scripts/v221_cpu_gate_ubuntu.sh 2>&1 | tee /mnt/g/ThreatStudy/v221_cpu_gate.log
```

Required `V221_CPU_AUTHORIZATION_PASS`. The script reruns the CPU tests, verifies code/data hashes, runs the actual pinned tokenizers, and saves `/mnt/g/ThreatStudy/v221_real_tokenizer_gate.json`. It writes a separate private authorization record in `outputs_v221/authorization.json`. **If any gate fails, do not run GPU.**

## Gate 1: 432-call archived-environment replay on RTX 5090

```bash
set -o pipefail
bash scripts/v221_replay_gpu.sh 2>&1 | tee /mnt/g/ThreatStudy/v221_replay.log
```

Review `outputs_v221/audit_summary.json` and replay byte/decision/validity agreement. Do not assume bitwise determinism. Mismatches are preserved and discussed.

## Gate 2: Arm C — fixed-choice candidate scoring (6,912 prompts)

```bash
set -o pipefail
bash scripts/v221_run_arm_gpu.sh C 2>&1 | tee /mnt/g/ThreatStudy/v221_arm_C.log
```

The logger records eight unnormalized end-of-turn-inclusive candidate scores and normalized probability mass for each call.

## Gate 3: Arm B — canonical JSON constrained decoding (6,912 prompts)

```bash
set -o pipefail
bash scripts/v221_run_arm_gpu.sh B 2>&1 | tee /mnt/g/ThreatStudy/v221_arm_B.log
```

## Gate 4: final independent CPU audit of GPU outputs

```bash
python3 -m v22core.gpu_handoff audit --root . \
  | tee /mnt/g/ThreatStudy/v221_final_audit.log
cp outputs_v221/audit_summary.json /mnt/g/ThreatStudy/v221_final_audit.json
```

`V221_FULL_MATRIX_PASS` is required for final inferences. A partial run can be inspected without changing the dataset or skipping completed checkpoints:

```bash
bash scripts/v221_status.sh > /mnt/g/ThreatStudy/v221_status.json
```

## Return evidence for independent review

Share `G:\\ThreatStudy\\v221_real_tokenizer_gate.json`, `v221_final_audit.json`, and selected GPU logs. To independently audit all new checkpoint rows, compress `outputs_v221/` (contains no model weights) into one ZIP and upload. Do not upload the original large APT archive unless requested.

## Scientific caveats

- Arm C changes the task to forced-choice likelihood scoring; its findings do not prove cardinality mediation.
- Arm B changes the allowed output language; it does not isolate formatting alone in a causal sense.
- The original v2.1.6 results remain the main historical empirical result and are never overwritten.
- Human gold labels, gold false-positive claims and OSF preregistration are absent.
- Do not redistribute publisher-sourced texts in the reference ZIP publicly without appropriate reuse rights.

To return full v2.2.1 results for independent review, run after GPU completion (or for an explicitly interim export):

```bash
python3 scripts/v221_export_results.py --out /mnt/g/ThreatStudy/ThreatStudy_v221_GPU_Results.zip
```

Upload that ZIP. It contains the new prediction checkpoints, metadata, authorization, audits and available v2.2.1 execution logs without pretrained weights or original publisher report archives.
