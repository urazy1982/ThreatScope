# ThreatScope E1 protocol v1.1.2 — revision record (2026-11-14)

**Status:** amended *before the first v1.1.2 GPU inference*. Earlier v1.1 and v1.1.1 starter/hand-off protocols have different prompt semantics. All historical A/B/C inference files are unchanged and immutable. The old v1.1.1 outputs must not be resumed or pooled with v1.1.2.

## Precisely defined treatments

Both use the historical Arm A system instruction and identical target serialization, targets in the same order and format, greedy generation, original model revisions, BF16/NF4 configuration and 96 output token cap. The ONLY distinction is the extra N1 format-demonstration line appended to the end of the N0 prompt:

```text
OUTPUT FORMAT EXAMPLE (not an answer to the targets): {"relevant":[]}
```

N0 includes no output example. N1's empty-list demonstration is **not behaviorally neutral**: possible empty-selection anchoring must be reported.

N0 and N1 are evaluated across the same 144 windows, three model families, two precisions and nine publisher strata (1,728 generations). The comparative treatment is a format illustration being present versus absent. Since these prompts are not identical to historical Arm A apart from the digit, E1 cannot identify the mediation mechanism of Arm C or make a pure causal claim relative to historical Arm A.

## Primary E1 analysis (exploratory internal freeze; no OSF claim)

1. For each window, model and condition, compare the eight binary selection decisions under BF16 and NF4: symmetric difference divided by 8. This is **cross-precision decision discordance**, not correctness.
2. Compute per-window `N1_discordance − N0_discordance` among windows where all four outputs are schema-valid (BF16/NF4 × N0/N1). Report four-way completeness and all malformed-output counts; never turn invalid JSON into a valid empty selection.
3. Aggregate equally over windows within each publisher, then equally over all nine publishers. Report exact two-sided publisher-level sign-flip tests (with sign-exchangeability assumption), **Holm-3** across the three primary model contrasts, and *descriptive* hierarchical publisher→report 95% bootstrap intervals (4,000 draws, fixed seed 20261114).
4. **Joint guardrails**: raw JSON validity, rate of valid empty selection, selection cardinality, original 288-slot human-reference F1 and the N1−N0 F1 contrast. Lower disagreement accompanied by all-empty outputs is not a successful mitigation claim.
5. Secondary exploratory interaction: within each publisher, (NF4−BF16 F1) under N1 minus (NF4−BF16 F1) under N0. Explicitly label multiplicity-unadjusted secondary tests and reference uncertainty.

## Data integrity

- Input JSONL, manifest, frozen model configuration and per-window SHA-256 must match original frozen data. A release-derived 288-row text-free sample has all 288 sentence SHA-256 bindings verified against the actual source texts before GPU execution.
- No duplicate-text label propagation: exactly 288 original sampled slots; 273 determinate adjudications; 15 undecidable excluded from relevance metrics. The 83 supplemental propagated occurrences stay outside the E1 reference evaluation.
- Tokenizer-ID gate: historical anchors must be tested for *all 28 distinct pairs* for each model under B and C, 24,192 total pairwise comparisons. One changed character does not imply one changed tokenizer ID.
- Real GPU requires exact historical software revisions, model commit identity where exposed, and NF4 linear layer quant-type verification.
- One smoke checkpoint arm followed by the sequential 12-cell full matrix; no cross-version resume.

## Interpretation restrictions

The corpus is still 72 previously used reports, drawn primarily from report beginning/end positions. No E1 result qualifies as independent external replication. Human-reference interpretations require sensitivity to inter-rater disagreement and absent report context. E1 does not test a secure deployment defense against adversarial prompt injection, and it does not distinguish a scoring-rule effect from the cardinality/instruction changes in Arm C. E2, E3 and E4 remain unexecuted.

## Tokenizer diagnostic hotfix — 2026-11-14

Corrected C8 report aggregation: maximum Hamming distance is computed as the maximum over windows, not the sum of per-window maxima. This is a **measurement-report bug fix only**, not a new prompt or GPU experimental protocol. See `TOKENIZER_DIAGNOSTIC_HOTFIX.md`.
