# ThreatScope — E2 matched singleton experiment (v0.1.2 tensor-input repair)

**Study:** ThreatScope (not “One Digit, Different Decisions”). Date: 2026-11-14.

## Immediate result

E1 (v1.1.2) has **1,728/1,728 completed checkpoints**, 1,675 valid responses, 53 invalid. Its primary across-precision N1−N0 disagreement effects (publisher-equal) were Qwen −0.175 pp (p=.957), Llama +2.474 pp (p=.359), Mistral +2.170 pp (p=.359). All Holm-3-adjusted p-values equal 1. E1 does not demonstrate a general N1 stability mitigation. See `notes/E1_INTERPRETATION.md`.

The user's 53 invalid outputs are *real experiment responses*, not checkpoint corruption. The original analysis treats invalid JSON as unusable, which can confound pooled F1 with format reliability. `scripts/e1_invalid_and_matched_quality.py` supplies an **additional CPU-only** intent-to-treat/valid-only/exact-four-way-matched comparison; it has not been executed against the user's actual E1 checkpoint directory on this server.

## E2 objective (post-E1, prospective freeze)

The historical v2.2.1 Arm C combined: (1) exact-one instruction, (2) singleton output space, and (3) teacher-forced likelihood **whole-continuation scoring**. E2 tests a new procedure that holds the **historical Arm C instruction, all 8 anchor prompts, model revision, candidate set, canonical JSON spelling, and EOS** fixed, while replacing whole-continuation scoring with **trie-constrained left-to-right greedy generation**. As a result, this is more controlled than unconstrained greedy generation; search procedure is the focal treatment.

The first primary contrast is Qwen, BF16 vs NF4, 144 original frozen windows × 8 prompt anchors × 2 precisions = **2,304 new GPU generations**. The full three-model extension would contain 6,912 generations. Reuse the already archived 6,912 Arm C scoring predictions—**do not rerun them**. All new E2 results are exploratory/post hoc relative to original v2.1.6; do not call this preregistration or causal mediation proof.

## Files

- `scripts/e2_singleton_gpu.py`: frozen-data guarded CUDA runner, checkpoint hashes and strict resume, exact singleton trie, pinned model/precision checks.
- `scripts/audit_e2.py`: CPU-only, actual pinned-tokenizer audit of every E2 generated suffix, with no model weights required.
- `scripts/analyze_e2.py`: direct paired greedy-vs-scoring comparison on 144 windows; per-anchor agreement, precision × procedure interaction, nine publisher exact sign flips, descriptive clustered bootstrap.
- `scripts/e1_invalid_and_matched_quality.py`: read-only E1 validity and matched-sample quality sensitivity.
- `reference/archived_armC_6912_winners.csv`: verified archived Arm C winning selections (no publisher report text); all 6,912 original record SHA-256 checks passed. The 432 published window effects reproduce to < 6e-17.
- `vendor/v22core/`: unchanged historical v2.2.1 prompt/tokenizer/scoring source modules.
- `vendor/e1_neutral_gpu.py`: unchanged frozen-input validator from v1.1.2.

**The kit does not include confidential source reports, model weights, original E1 checkpoint files or new GPU inference results.**

## Install on Ubuntu / WSL (from Windows Downloads first)

Download `ThreatScope_E2_v0_1_2_Tensor_Fix_2026-11-15.zip` to `C:\Users\uraz\Downloads`.

```bash
mkdir -p ~/threat-study/ThreatScope_E2_v0_1_2
unzip -o /mnt/c/Users/uraz/Downloads/ThreatScope_E1_Review_E2_Factorial_v0_1.zip \
  -d ~/threat-study/ThreatScope_E2_v0_1_2
cd ~/threat-study/ThreatScope_E2_v0_1_2
source ~/threat-study/.venv/bin/activate
bash run_preflight.sh
```

The preflight is **CPU-only** and requires your original frozen inputs at `~/threat-study/aptcorpus_v214_work/outputs/prepared/`.

### Follow-up E1 anomaly audit, no GPU

```bash
bash run_e1_diagnostic.sh
cat ~/threat-study/ThreatScope_E2_v0_1_2/results/E1_review/E1_DIAGNOSTIC_SUMMARY.json
```

Reports malformed output errors by configuration, intent-to-treat F1, valid-only F1 (different denominator), and exact-four-way-matched F1 (same denominator), from the original 273 determinate labels. It does **not** re-run E1.

### E2 GPU smoke (when GPU idle)

```bash
bash run_smoke.sh
```

This performs Qwen BF16 on 2 frozen windows × 8 anchors = **16 actual constrained greedy generations**, followed by a checkpoint/tokenizer audit. It refuses to run when another GPU compute process is present. No tmux and no background scheduling.

### E2 complete Qwen-only experiment

```bash
bash run_full.sh
```

Runs/resumes 1,152 BF16 + 1,152 NF4 generations sequentially in a **new E2-specific directory**, then audits and analyzes results. Never mix E1 and E2 checkpoints. `run_full.sh` requires the 16-checkpoint smoke audit first.

After completion, look at:

- `~/threat-study/ThreatScope_E2_v0_1_2/results/E2_analysis/E2_summary.json`
- `~/threat-study/ThreatScope_E2_v0_1_2/results/E2_analysis/E2_by_publisher.csv`
- `~/threat-study/ThreatScope_E2_v0_1_2/results/E2_analysis/E2_by_window.csv`

Optional: `bash export_small_reports_to_H.sh` copies the two summary JSON reports (when present) to `/mnt/h/ThreatScope/`; no bulk checkpoint copying.

## CPU testing already executed on assistant server

- 6/6 real frozen-data E2 preflight configurations PASS (3 models × 2 precisions).
- Historical Arm C original-record SHA-256: 6,912/6,912 PASS.
- Historical Arm C prompt SHA-256 against original full-text frozen windows: 6,912/6,912 PASS.
- Published Arm C per-window numerical replay: 432/432 PASS.
- E2 2,304-record synthetic software analysis and tamper-rejection rehearsal PASS. **Synthetic checkpoints are not empirical GPU evidence, were deleted, and are not in this release.**
- CPU unit-test suite PASS (record count in `notes/CPU_VALIDATION.md`).

## Publication limits

This is a post-E1 extension (not a prospective externally registered study). A change in greedy vs scoring decisions under equal singleton candidate spaces supports a decoding/search-procedure contribution but cannot alone establish general performance, correction, or complete mediation. E3 independent interior-report replication remains necessary for broad external-validity claims. E1 human-reference data contain imperfect expert adjudication; do not present them as uncontested gold labels.
