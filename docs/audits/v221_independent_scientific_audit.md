# Independent scientific audit — ThreatStudy v2.2.1 (2026-11-13)

**Working title:** *One Digit, Different Decisions: Quantization-Dependent Example Sensitivity in Structured Cyber-Threat Intelligence Relevance Selection*

## Scope and disposition

**Conclusion:** `INDEPENDENT_CHECKPOINT_TO_STATISTICS_PASS`. All 14,305 exported-file SHA-256 digests verified. All 14,256 new experiment checkpoints validated for record integrity, model revision, frozen input/window identity, candidate consistency and the applicable JSON/likelihood rules. The 432 Arm A environment-replay predictions matched the archived v2.1.6 records exactly in raw text, decision and validity, independently compared with the immutable baseline archive. No new GPU inference or raw-report acquisition was attempted by this auditor.

The frozen sample contains 144 windows in 72 reports (8 per publisher, two windows per report) from nine source/publisher categories. All six model-by-precision cells are complete for both mechanism arms B and C. The distinct 432-call replay is also complete.

## Primary results — independent recomputation

All effects are NF4 minus BF16 for the frozen, source-equal, report-equal interaction in percentage points (pp). Two-sided exact sign-flip p values enumerate 2^9=512 publisher signs. Holm-3 corrects the three models within an arm. Holm-6 is the additional sensitivity across all six B/C primary tests. Percentile confidence intervals are descriptive hierarchical publisher-then-report bootstrap intervals (10,000 resamples, independent fixed seeds).

| Arm | Model | NF4–BF16 Δ (pp) | Exact p | Holm-3 | Holm-6 | 95% hierarchical CI (pp) |
|---|---|---:|---:|---:|---:|---|
| B — canonical JSON | Qwen2.5-3B | +11.42 | 0.00391 | 0.01172 | 0.02344 | [8.17, 14.79] |
| B — canonical JSON | Llama-3.2-3B | +7.16 | 0.00391 | 0.01172 | 0.02344 | [3.53, 10.69] |
| B — canonical JSON | Mistral-7B | +4.85 | 0.01172 | 0.01172 | 0.03516 | [2.07, 7.50] |
| C — single-choice likelihood | Qwen2.5-3B | +0.30 | 0.78516 | 0.78516 | 0.78516 | [−1.69, 2.28] |
| C — single-choice likelihood | Llama-3.2-3B | +6.94 | 0.00391 | 0.01172 | 0.02344 | [4.96, 9.03] |
| C — single-choice likelihood | Mistral-7B | +2.48 | 0.01563 | 0.03125 | 0.03516 | [0.89, 4.07] |

All six values exactly reproduce the archive's reported raw effects and within-arm p corrections. Five of six controls show positive, statistically detectable interactions even under Holm-6; Qwen Arm C is inconclusive, **not proved null** (its bootstrap upper endpoint is above the pre-specified 2-pp meaningful-effect threshold).

## Relation to v2.1.6 free generation (Arm A)

| Model | A: free | B: constrained | C: single-choice | B−A | C−A |
|---|---:|---:|---:|---:|---:|
| Qwen2.5-3B | +11.36 | +11.42 | +0.30 | +0.06 | −11.06 |
| Llama-3.2-3B | +4.97 | +7.16 | +6.94 | +2.18 | +1.97 |
| Mistral-7B | +6.01 | +4.85 | +2.48 | −1.17 | −3.53 |

Paired publisher-level **exploratory** sign-flip tests on the arm differences give Qwen C−A p=0.00391 and B−A p=0.85156. Llama B−A p=0.00781. Mistral C−A p=0.00781. These extra tests were not a separate registered confirmatory family; see `independent_arm_comparisons.csv` for all effects, exact p values and bootstrap CIs.

The result supports an interaction under schema-constrained outputs for all three models. It supports an interaction under single-choice likelihood scoring for Llama and Mistral but not detectably for Qwen. The disappearance of Qwen's effect in Arm C **cannot by itself establish cardinality mediation**: Arm C changes the relevance instruction, imposes a forced choice, and uses teacher-forced candidate log-likelihoods rather than free/grammar-constrained generation. Arm B can also affect model decisions in ways beyond syntax correction.

## Additional output-quality and scoring checks

All 6,912 Arm B records have valid canonical JSON and no 96-token generation-cap hits. All 6,912 Arm C records select one valid index and have finite eight-candidate scores, mass vectors summing to one and correct argmax tie-breaking. Among the 6,912 Arm C calls, exactly **one** has a tied maximum (Llama NF4). No Arm C call from Qwen or Mistral has an exact tie.

| Model | Arm B mean number selected: BF16 → NF4 | Arm B exact singleton example copies: BF16 → NF4 | Arm C exact example choices: BF16 → NF4 |
|---|---|---|---|
| Qwen2.5-3B | 3.234 → 4.128 | 21 → 122 | 147 → 150 |
| Llama-3.2-3B | 4.286 → 3.890 | 0 → 1 | 64 → 134 |
| Mistral-7B | 4.247 → 3.977 | 16 → 25 | 146 → 171 |

As a **secondary** Arm C sensitivity analysis, using the full eight-way score-softmax probability mass instead of hard argmax gives Δ = +0.99 pp for Qwen (exact p=0.13672), +2.71 pp for Llama (p=0.00391), and +1.99 pp for Mistral (p=0.00391). These p values are unadjusted and secondary.

## Scientific caveats and publication position

1. **Provenance:** The result ZIP includes frozen authorization, source hashes, local real-tokenizer checks, GPU software lock and per-cell metadata. It does **not** contain original full publisher reports, the external ~10.7 GB source archive or pretrained weights. The audit reproduces statistics from stored predictions, not neural inference independently.
2. **Protocol:** v2.2.1 has a locally recorded amendment and SHA-256 freeze, but **no verified OSF preregistration**. The new arms were designed after v2.1.6 outcomes were available. Disclose this and avoid calling them prospective external preregistrations.
3. **Gold standards:** Human relevance labels were **not** supplied. The study measures decision sensitivity, not relevance accuracy, false-positive consequences or improved threat-intelligence utility.
4. **Inference:** Only nine publisher groups exist. Bootstrap CIs are descriptive. Exact publisher sign flips are the primary tests under their exchangeability assumptions. Do not equate statistical significance with practical quality impact.
5. **Interpretation:** An absent significant effect is not proof of no effect, and significance differences between arms are not themselves tests of arm contrasts. All comparisons should state their design and exploratory status.

**Manuscript recommendation:** Use the complete v2.1.6 A results plus B/C mechanisms as a single research story with explicitly **model-dependent** behavior. Emphasize that constrained JSON is not sufficient to eliminate prompt-index sensitivity, while Qwen's reaction changes sharply with the forced-choice/scoring procedure. Before asserting the specific causal mechanism for Qwen, a narrowly targeted same-prompt, same-output-space control would be valuable; this is optional for the current descriptive manuscript, but necessary for a strong mediation claim.

## Reproduce the audit

The independently authored scripts `independent_recompute.py` and `compare_arms.py` use Python's standard library. To run them from the supplied two original ZIPs, run `run_independent_audit.py --results-zip <ThreatStudy_v221_GPU_Results_Final.zip> --release-zip <ThreatStudy_v221_GPU_Readiness.zip> --out <directory>`. The wrapper recovers the immutable baseline v2.1.6 checkpoint archive from the v2.2.1 release, checks all file hashes and all checkpoint records, reproduces the publisher-level statistics, then produces source-, window- and arm-level CSVs with bootstrap intervals.
