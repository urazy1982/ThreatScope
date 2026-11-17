# ThreatScope E1/E2 — independent text-free evidence audit

## Audit outcome

**PASS for decision-level reproduction; limited for original inference provenance.** All 10 input payload files listed in `SHA256SUMS.txt` verify. The exported table contains 1,728 unique E1 decisions and 2,304 unique E2 prompt decisions; there are no duplicate compound keys. E1 reports 1,675 valid and 53 invalid responses, precisely matching `E1_full_audit.json` at the level of each of the 12 cells.

Using an independently written script (`independent_check.py`), we recomputed from E2 prompt-level choices:

| Measure | Independent result |
| --- | ---: |
| BF16 greedy/scoring agreement | 1122/1152 = 97.3958% |
| NF4 greedy/scoring agreement | 1136/1152 = 98.6111% |
| Publisher-equal greedy NF4-BF16 effect | +0.694444 pp |
| Publisher-equal scored NF4-BF16 effect | +0.297619 pp |
| Greedy minus scoring difference-in-differences | +0.396825 pp |
| Exact nine-publisher, two-sided magnitude-sensitive sign-flip p | 0.359375 |

All 144 `E2_by_window.csv` rows and nine `E2_by_publisher.csv` rows reconcile with recomputation from the 2,304 prompt-level choices. Per-window index association uses D=(n diagonal prompt-digit matches−1)/7. All E2 prompt digits 0–7 occur once per window and precision. The E1 decision table also reproduces the original direct stability summary (Qwen −0.175265 pp, Llama +2.474285 pp, Mistral +2.170139 pp) on respectively 130, 110 and 144 complete matched windows. Invalid and valid-empty E1 outputs remain separate.

## Minor source reporting discrepancy

`E2_summary.json` records **six positive, two negative, one zero** publisher effects. In the exported publisher table, SentinelLabs has an effect of `2.1684043449710089e-16` pp, numerically zero. Under a reasonable tolerance (1e-10 pp), the correct publisher sign count is **five positive, two negative, two zero**. This does not alter the magnitude-sensitive sign-flip p-value of 0.359375. Do not overinterpret sign counts computed on floating-point residuals. Correct the descriptive publisher sign count in the analysis script or manuscript.

## What the current package cannot establish

- Original raw E1/E2 checkpoint bodies are not distributed; hashes in the CSV are identifiers, not proof they correspond to an independently available model execution.
- Original report sentences and private human labels are absent. Human-reference F1 is supplied as a derived result and cannot be independently rederived from this text-free package alone.
- The exact hierarchical bootstrap CI was not independently recalculated in this audit; reproduce it from the method's documented sampling procedure and seed before making a full independent CI certification claim.
- Greedy and historical prompt hashes in `E2_per_prompt_decisions_2304.csv` differ; raw prompt equivalence must be demonstrated using the archived runner, not asserted from these hash strings.
- E2 supports robust single-output decision selection across greedy versus scorer procedures but does **not** isolate the joint cardinality/instruction mechanism.

## Recommendation

The evidence export is suitable for a public, **text-free, decision-level reproducibility supplement** once confidentiality/provenance checks and the tiny sign-count correction are addressed. Preserve original E1/E2 checkpoints and models' exact versioned code privately. Prioritize E3 external replication, and if a strong mechanism claim is desired, run the two missing instruction-by-cardinality factorial cells.
