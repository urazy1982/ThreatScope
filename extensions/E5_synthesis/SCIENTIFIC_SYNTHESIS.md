# ThreatScope — E5 integrated scientific synthesis

**Status:** CPU cross-study reconciliation completed using archived E1–E4 decisions. No new GPU inference.

## Evidence hierarchy and original estimands

- **Historical Arms A–C:** The principal estimand is example-digit dependence and its NF4–BF16 interaction. The nine-publisher historical archive and original confirmatory / amended analysis remain distinct from extensions.
- **E1:** N0 is a no-example prompt, N1 adds the index-free example. The frozen primary estimand is N1−N0 BF16/NF4 decision disagreement **on complete valid four-cell windows**, with equal window weighting within publisher. This is **not** the original digit-dependence estimand. Alternative window→report→publisher weighting and invalid-as-empty results are sensitivity analyses. E1 cannot be described as successful mitigation. Llama BF16 validity moved from 111/144 (N0) to 144/144 (N1), an exploratory configuration-specific format compliance observation.
- **E2:** The same Qwen historical Arm C singleton output space under greedy versus candidate likelihood scoring. Shared candidate prefixes make the procedures almost equivalent by construction. Report only as decoding-procedure robustness, not causal mechanism isolation.
- **E3:** New interior windows from previously unused reports in the *same* APT archive. Eight publishers, deliberately excluding Bitdefender; uneven counts, historical publisher overlap and retrospective sampling must be disclosed. This is a within-archive report holdout, **not an independent corpus**.
- **E4:** FP4 versus NF4 nominal four-bit format comparison in Qwen and Llama on the E3 windows; exploratory, with 47/576 Qwen FP4 malformed responses. Contrast is format-dependent deployment behavior, not bit-width change or accuracy improvement.

## Main effect summary (percentage points)

| Study / effect | Qwen | Llama | Mistral | Interpretation |
|---|---:|---:|---:|---|
| Original Arm A NF4−BF16 | +11.36 | +4.97 | +6.01 | Historical example-index interaction |
| E1 N1−N0 disagreement | −0.18 | +2.47 | +2.17 | Complete-case frozen estimand; none significant |
| E2 greedy−scoring precision interaction | +0.397 | — | — | Exploratory p=0.3594; decoder robustness only |
| E3 NF4−BF16 | +18.67 | +5.27 | +1.95 | Eight-publisher within-archive report holdout |
| E4 FP4−NF4 | +8.48 | +2.21 | — | Two exploratory p-values 0.1719 and 0.1953; Holm both 0.3438 |

**E3 multiplicity:** exact exploratory p: Qwen 0.0078125, Llama 0.046875, Mistral 0.203125; Holm across three: 0.0234375, 0.09375, 0.203125. Qwen replicates in this within-archive holdout; the other families do not clear this family-wise threshold.

**E2 numerics:** Scoring delta +0.297619 pp; greedy delta +0.694444 pp; difference +0.396825 pp; agreement 97.3958% BF16 and 98.6111% NF4. Publisher sign tally corrected using numerical tolerance: 5 positive, 2 negative, 2 tied (raw float tally wrongly 6/2/1). Exact p unchanged.

**E4 invalid handling:** The original analysis treats malformed selections as empty for the primary precision contrasts. Full-window validity sensitivity analysis reports Qwen +8.70 pp on 53 windows and Llama +1.76 pp on 70 windows, both inconclusive. Do not equate increased dependence or invalid outputs with greater operational risk without external relevance evidence.

## Required manuscript corrections

1. Replace claims that E1 mitigates digit sensitivity; it tests two index-free prompts and a different disagreement estimand.
2. Show frozen E1 complete-case analysis first, then report-equal and invalid-as-empty sensitivity; identify Llama's sign reversal in the latter. Explicitly report format-validity rates.
3. Limit E2 to a brief procedural robustness subsection; do not infer cardinality versus instruction mechanism.
4. Present E3 as an eight-publisher report holdout within the same archive. Do not say independent-corpus, temporal, or fully prospective validation. State v0.3 posthoc sampling amendment and publisher distribution.
5. Present E4 as same-bit-width FP4–NF4 exploratory comparison. Discuss parser failures separately and adjusted p-values. Do not infer FP4 intrinsically worse.
6. Preserve the original 288 human annotated slots, disclose adjudication asymmetry, and keep propagated 371-slot calculations supplementary.
7. Align every p-value with publisher sign-flip exchangeability assumptions and multiplicity family; do not turn nonsignificance into equivalence.
8. Correct historical manuscript formatting/denominator errors, including Arm C one tie among 6,912 prompt conditions / 55,296 candidate scores.
9. Provide public text-free decisions and hashes, archival provenance, code to replay exact statistics, and note restricted historical source/annotation inputs.

## Remaining publication risks

There remains no validated mediation explanation for the Arm C attenuation (instruction and cardinality not separated), no independent publisher/corpus holdout, and human-label disagreements weaken claims of CTI usefulness. These must be acknowledged even if all exported numerical checks pass.

## Reproducibility claim boundaries

This package independently checks exported decision records and the relationships among published summaries. It does not independently rerun GPU inference, recover unreleased human labels, or establish that selected E3 reports are semantically unrelated to all historical reports.
