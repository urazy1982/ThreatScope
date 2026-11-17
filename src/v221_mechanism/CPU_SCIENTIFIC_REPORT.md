# Independent CPU Scientific Report — ThreatStudy v2.2-Core

**Manuscript title:** *One Digit, Different Decisions: Quantization-Dependent Example Sensitivity in Structured Cyber-Threat Intelligence Relevance Selection*

**Evidence classification:** historical v2.1.6 checkpoint reanalysis + new CPU software experiments + explicitly synthetic v2.2 test data. **No new model inference.**

## Verified inputs and scope

- Entire archived v2.1.6 matrix: 6,912/6,912 raw/checkpoint records cryptographically checked, model and revision identities validated, parsers rerun; no missing/extra example checkpoints.
- Dataset identity: `461682f329a5cca95715d6d7a12356dddb3f38f3adf0e221a2443bdecfdd354e`; 144 windows, 72 reports, 9 publishers, 8 index examples, 3 models, 2 precisions.
- Old tokenizer gate is consistent with **actual archived** prompt token counts: Qwen 1,285; Llama 919; Mistral 1,367; 0 mismatched index-variant lengths.
- Old corpus provenance gate matches source revision and dataset/input fingerprints. The historical SMAH comparison remains selected-window based, not definitive semantic independence.

## The central algebraic decomposition

For each eight-prompt window let T be the number of self-example index inclusions (diagonal hits across eight prompts) and C the sum of all selected-index counts across these prompts. The originally used balanced estimator simplifies exactly to:

`D = (T - C / 8) / 7`.

For the NF4-minus-BF16 difference, `Delta = Delta(T)/7 - Delta(C)/56`. We independently verified this identity for all 432 model-window pairs and reproduced the original source-equal effects and Holm-adjusted exact p values.

| Model | NF4−BF16 diagonal-hit contribution | NF4−BF16 total-cardinality contribution | Net interaction |
|---|---:|---:|---:|
| Qwen2.5-3B | +24.50 pp | −13.14 pp | **+11.36 pp** |
| Mistral-7B | +1.39 pp | +4.63 pp | **+6.01 pp** |
| Llama-3.2-3B | −1.39 pp | +6.36 pp | **+4.97 pp** |

These are **descriptive algebraic contributions**, not identified mediation effects. For Llama, the raw own-example hit count actually **decreases** by 14 under NF4. For Mistral, the raw own-example count rises by only 14 but total selections shrink by 373. Qwen rises by 247 own-example hits but also produces 1,060 more selections overall. Never characterize all three patterns as universal literal copying.

## Exploratory cardinality-normalized sensitivity

An additional posthoc statistic assigns mass `1 / cardinality` to each selected index in every output, zero to any empty selection, and recomputes the balanced index contrast. It is an **analysis of existing selected sets**, not the Arm C choice likelihood or a constrained generation run.

| Model | Original NF4 interaction | Uniform-set-mass interaction | Exact publisher p | Holm p (3 models) |
|---|---:|---:|---:|---:|
| Qwen2.5-3B | +11.36 pp | **+9.73 pp** | 0.003906 | 0.011719 |
| Mistral-7B | +6.01 pp | **+2.03 pp** | 0.015625 | 0.015625 |
| Llama-3.2-3B | +4.97 pp | **+1.66 pp** | 0.007812 | 0.015625 |

The direction survives this particular posthoc normalization, but the effect shrinks substantially in Mistral and Llama. These p-values are **exploratory**, as the endpoint was introduced after seeing the original data.

## Conditional cardinality-preserving index-exchangeability references

10,000 synthetic draws were generated **per model**, keeping each archived output's exact number of selected indices but randomizing which positions were selected. This is a constructed reference distribution under independent index exchangeability, not experimental randomization, not publisher-level source inference, and not a mechanism-identifying test.

| Model | Observed contrast | Synthetic null 95% interval | Illustrative tail fraction |
|---|---:|---:|---:|
| Qwen2.5-3B | +11.36 pp | −3.62 to +3.62 pp | 0.00010 |
| Mistral-7B | +6.01 pp | −4.30 to +4.33 pp | 0.00480 |
| Llama-3.2-3B | +4.97 pp | −4.15 to +4.18 pp | 0.01940 |

This illustrates that cardinality magnitudes alone, under fully exchangeable index positions, do not predict the observed diagonal associations. It does **not** settle why models show index-dependent behavior.

## Source-level and validity sensitivity

The original v2.1.6 primary exact p-values remain 0.003906 for Qwen, 0.007812 for Mistral and 0.015625 for Llama (Holm: 0.011719, 0.015625, 0.015625). Invalid-output counts remain Qwen 69 BF16 vs 5 NF4, Llama 2 vs 11, Mistral 0 vs 0. All three primary interactions remain positive under leave-one-publisher-out means; see `results/cpu_main_results.json`.

Exploratory source-level contrasts between models show Qwen's effect exceeds Mistral and Llama; these model-difference comparisons are not preregistered or adjusted for all exploratory tests.

## CPU verification of planned new arms

- **Arm B:** All 256 unique sorted-index JSON outputs pass the original parser, a token-level prefix trie reaches exactly the 256 outputs with the mock tokenizer, invalid syntax and duplicates are rejected. Actual Hugging Face tokenizer and CUDA generation have **not** run.
- **Arm C:** All eight canonical singleton candidates, end-of-turn marker checks, batched teacher-forced log probability, serial-vs-batch equivalence on a CPU toy LM, softmax mass, non-normalized score sums, finite-score checks and deterministic lowest-index tie rules pass. Actual model-weight likelihoods have **not** been computed.
- **v2.2 simulated full integration:** 13,824/13,824 deliberately synthetic B/C records independently validated, with tamper and missing-record rejection. Synthetic model results must **never** be reported as empirical findings.
- **Environment replay selection:** Exactly 432 planned Arm A calls selected deterministically (one window per publisher × eight prompts × six model–precision cells); no environment replay GPU calls were executed.

## Scientific recommendation and limitations

The strong Qwen behavior and the model-specific contribution of selection-set size make Arm C **high priority**. Arm B remains important to isolate syntactic constraint effects from free-format generation. Those real model runs are indispensable for a mechanism interpretation. Revisions to the draft v2.2 protocol, external OSF registration, and real local tokenizer-template gate remain pending. Human-relevance gold labels, independent double annotation, and additional quantization methods are not part of the short-cycle work.

The manuscript should present v2.1.6 as its established empirical result, the CPU decomposition as an exact retrospective diagnostic, and any future B/C findings as newly collected evidence only after separately frozen and fully checked inference.
