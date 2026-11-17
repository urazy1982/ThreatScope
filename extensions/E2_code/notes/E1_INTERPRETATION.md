# E1 independent statistical interpretation — supplied aggregate output

Source: user-provided output from `bash run_analysis_only.sh`, protocol `ThreatScope-E1-v1.1.2-minimal-example-intervention`. The individual E1 GPU checkpoint bytes were **not** uploaded in this turn. The numbers below were independently reconciled arithmetically from the pasted audit and CSV tables, not raw reanalyzed on this server.

**Full matrix:** 1,728/1,728 checkpoint files, 1,675 valid JSON responses (96.93%), 53 malformed or invalid (3.07%). No generation cap was reported as reached.

## Main direct stability estimand

N1-minus-N0 in paired BF16-vs-NF4 decision disagreement; negative means less precision disagreement. Only complete four-way-valid windows included. Publisher equal, 9 groups; p values exploratory sign-flips requiring publisher sign-exchangeability.

| Model | Four-way-valid windows | Effect (pp) | Descriptive 95% CI (pp) | Exact p | Holm-3 |
|---|---:|---:|---:|---:|---:|
| Qwen2.5-3B | 130/144 | −0.175 | [−5.297, +5.914] | .9570 | 1.000 |
| Llama-3.2-3B | 110/144 | +2.474 | [−4.357, +8.173] | .3594 | 1.000 |
| Mistral-7B | 144/144 | +2.170 | [−2.431, +6.944] | .3594 | 1.000 |

No model establishes a neutral-prompt precision stability benefit. Non-significance is **not** evidence of equivalence. E1 tests a neutral-format example and *does not directly manipulate the eight index anchors*, so it is not a replication of Arm A's main index-sensitivity estimand.

## Output schema validity

| Model/precision | N0 valid | N1 valid | Key caution |
|---|---:|---:|---|
| Qwen BF16 | 138/144 | 141/144 | BF16 valid empty fraction 21.0% (N0) vs 12.1% (N1) |
| Qwen NF4 | 140/144 | 138/144 | Essentially no valid empty selections |
| Llama BF16 | 111/144 | 144/144 | 33→0 invalid; major format reliability difference |
| Llama NF4 | 144/144 | 143/144 | Slight validity decline |
| Mistral BF16 | 144/144 | 144/144 | Format ceiling |
| Mistral NF4 | 144/144 | 144/144 | Format ceiling |

The very large Llama BF16 compliance difference deserves an independent analysis of invalid-response causes, especially because it also influences reported F1. The new CPU audit script provides a paired format-validity inventory.

## Relevance F1: guardrails, not definitive quality truth

Pooled F1 on 273 determinate labels originally adjudicated in 288 slots. N0→N1 changes: Qwen BF16 +3.33 pp, Qwen NF4 +2.84 pp; Llama BF16 +4.15 pp, Llama NF4 +2.04 pp; Mistral BF16 +1.26 pp, Mistral NF4 −0.91 pp. These are descriptive, not proof of operational improvement.

The original v1.1.2 analysis encodes malformed JSON as a failed extraction with zero selected indices (not a *valid* empty response). This is a legitimate intent-to-treat utility metric but confounds formatting failures with sentence-label performance. Report separately: format-validity, ITT F1, valid-only F1, and F1 over *identical all-four-valid labeled windows*. The latter cannot be computed from the aggregate paste alone and requires the original E1 checkpoints on Ubuntu.

## No contamination

Historical Arm C remains frozen; E2 must not change its prompt, source windows, candidate spelling or scorer. New conditions are separately versioned and identified as post-hoc mechanism experiments.
