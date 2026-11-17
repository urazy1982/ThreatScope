# ThreatStudy v2.1.6 — Independent Scientific Audit

**Scope:** User-uploaded `ThreatStudy_v216_Complete_Results.zip` (3 models × 2 precisions × 8 prompts × 144 windows = 6,912 checkpoint records). This audit was independently computed from the per-call records, not merely copied from the supplied summary. All numbers below refer to the staged nine-publisher APT corpus. The experiment has no gold relevance labels.

## Integrity and completion

- **6,912/6,912 checkpoints independently read and validated.** Verified every raw-response hash, checkpoint record hash, frozen input hash, run-cell identity hash, model name, precision, anchor index and model revision. Independently parsed each response and verified the saved `valid` and `indices` values.
- Verified 144 unique windows and the frozen prepared input/configuration SHA-256 against the supplied manifest. The study dataset fingerprint is `461682f329a5cca95715d6d7a12356dddb3f38f3adf0e221a2443bdecfdd354e`.
- Verified the hashes of all three supplied analysis CSVs; independently reproduced their model-level estimates and exact publisher-level p-values.
- **Boundary:** The archive does not contain the original 10.7 GB publisher reports, the historical full SMAH reports, or a separately archived signed GPU authorization record. Their full contents/independence and the authorization itself therefore cannot be independently revalidated from this results ZIP. Logs include an authorization digest and the reported GPU gate result, but the underlying authorization file is not in this export.

## Primary outcomes

For each eight-sentence window, the **prompt-specific inclusion contrast** is the probability the example's index is selected under its own example, minus selection of that same index under the seven other examples, averaged over eight index positions. The primary interaction is this contrast under NF4 minus the contrast under BF16. It is not a gold-label accuracy score or proof of literal copying.

| Model | BF16 contrast | NF4 contrast | NF4 minus BF16 | Exact 9-source two-sided sign-flip p | Holm p | Source signs |
|:--|--:|--:|--:|--:|--:|:--|
| Qwen2.5-3B | +4.19 pp | +15.55 pp | **+11.36 pp** | 0.00390625 | **0.01171875** | 9 positive, 0 negative |
| Mistral-7B | +3.19 pp | +9.20 pp | **+6.01 pp** | 0.00781250 | **0.01562500** | 8 positive, 1 negative |
| Llama-3.2-3B | −5.18 pp | −0.21 pp | **+4.97 pp** | 0.01562500 | **0.01562500** | 7 positive, 2 negative |

All three adjusted p-values are below 0.05 under the **specified** symmetric publisher sign-flip null. The source count is nine, so inference is discrete and limited by small-cluster assumptions. This is not a random-assignment test of publisher effects, and it cannot guarantee generalization to unseen publishers.

Source-then-report bootstrap CIs in the supplied analysis (not independently bootstrapped): Qwen +8.13 to +15.04 pp; Mistral +2.90 to +8.83 pp; Llama +1.69 to +8.36 pp. These should not be treated as a replacement for the exact source-level analysis.

## Format and behavioral diagnostics (independently computed)

| Model | Precision | Invalid / 1152 | Mean selected indices | Example index selected | Exactly singleton example | Pairwise prompt disagreement |
|:--|:--|--:|--:|--:|--:|--:|
| Qwen | BF16 | **69** | 3.23 | 44.0% | 1.30% | 41.8% |
| Qwen | NF4 | **5** | 4.15 | 65.5% | 10.33% | 66.2% |
| Mistral | BF16 | 0 | 4.34 | 57.0% | 1.39% | 49.7% |
| Mistral | NF4 | 0 | 4.02 | 58.2% | 2.17% | 54.2% |
| Llama | BF16 | 2 | 4.31 | 49.3% | 0.00% | 49.8% |
| Llama | NF4 | 11 | 3.86 | 48.1% | 0.09% | 55.0% |

Note that **marginal example-index selection** (e.g., 48.1% under NF4 vs. 49.3% BF16 for Llama) is not the same estimand as the **matched prompt-specific inclusion contrast**. This explains why its positive interaction does not imply a higher overall probability of selecting the example index.

Qwen also experiences a large shift in response cardinality (+0.92 selected indices) and format compliance (69 BF16 invalid versus 5 NF4 invalid). Invalid responses are treated as empty under the pre-specified operational metric; this is a meaningful part of the observed result, not a mere cosmetic defect. Report both dimensions separately.

All three models show higher within-window prediction disagreement across the eight example prompts under NF4. This supports the descriptive claim of increased prompt sensitivity but does not, alone, identify *why* the sensitivity increased.

## Valid-only sensitivity

Requiring all 16 responses for a window (8 BF16 and 8 NF4) to be valid leaves 119 Qwen windows, 135 Llama windows, and all 144 Mistral windows. Source-equal effects (with source means computed from retained windows rather than the original report-weighted primary sample) are:

| Model | Retained windows | Interaction | Exact publisher sign-flip p |
|:--|--:|--:|--:|
| Qwen | 119/144 | +9.75 pp | 0.00390625 |
| Mistral | 144/144 | +6.01 pp | 0.00781250 |
| Llama | 135/144 | +4.97 pp | 0.01562500 |

**Post-hoc qualification:** This complete-valid-window restriction is not the primary estimator, changes source/report weights and can introduce selection bias. It is supportive robustness evidence only.

## Scientific interpretation and limitations

1. **Supported:** In this independent publisher-focused CTI corpus, the prespecified balanced eight-index output example intervention elicits a larger *prompt-specific inclusion contrast* in NF4 than BF16 for all three model families. The primary results are reproducible from the submitted checkpoints, and publisher-level sign-flip p-values survive Holm correction.
2. **Not supported:** Universal literal example copying, improved/deteriorated CTI classification accuracy, or a general principle that all quantization increases errors. In particular, Llama's average contrast remains approximately zero/negative after NF4; its **change** is positive.
3. **Format confound:** Qwen BF16 produces substantially more invalid JSON. The all-attempt primary effect and the valid-only sensitivity differ, although direction persists.
4. **Output cardinality:** The mean number of selected indices changes markedly for Qwen, and in the opposite direction for Llama/Mistral. Matched inclusion contrast controls for each index's overall baseline rate across the eight prompts, but cannot by itself distinguish imitation mechanisms from prompt-dependent cardinality and other response-policy changes.
5. **Source independence:** Nine named publishers are better than the earlier five source groups. However, publisher-level effects need not be exchangeable or independent if reports syndicated/shared content. The available prior near-duplicate screen was not a definitive semantic-independence test.
6. **Reproducibility boundary:** Model revisions and software environments are recorded. The original source archive is not included here. Tokenizer preflight and authorization evidence are reported in logs but their underlying standalone records are not part of the export.
7. **Research chronology:** v2.1.6 was designed after inspection of earlier SMAH findings. Call this a planned cross-corpus follow-up, not a fully independent preregistration conducted before any related model results were known.

## Suggested manuscript claim

**“Across nine publishers, balanced JSON example-index interventions yielded significantly larger prompt-specific inclusion contrasts under NF4 than BF16 in three open-weight instruction models, using exact publisher-level tests with multiplicity correction. The pattern is not reducible to universally copying the demonstrated singleton index; model-specific output-cardinality and JSON-validity shifts remain important alternative mechanisms.”**

A suitable title is *One Digit, Different Decisions: Quantization-Dependent Sensitivity to Structured Output Examples Across Cyber-Threat Reports*. The next highest-value work is a fixed-cardinality/structured-decoding control and a stronger full-report independence audit; neither requires re-running the completed 6,912 inference calls unchanged.
