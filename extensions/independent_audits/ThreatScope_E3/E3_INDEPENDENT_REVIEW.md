# ThreatScope E3 v0.4 — Independent CPU Reanalysis

## Scope and provenance

Input archive: `ThreatScope_E3_v0_4_Complete_GPU_Results.zip` supplied by the researcher. The independent script in this bundle opens the original ZIP, verifies the manifest-tracked release-code hashes, validates JSON checkpoint and raw-response SHA-256 digests, compares checkpoint fields to exported text-free decisions, recalculates example-index dependence per window, aggregates publisher-equal effects, and enumerates all 256 eight-publisher sign-flip assignments. It does not rerun neural inference.

## Integrity and result status

* ZIP integrity PASS (3,490 members)
* 11/11 release code and config manifest hashes PASS
* 3,456/3,456 checkpoints present; six cells of 576
* 0 checkpoint structural/hash/parser discrepancies under historical parser (valid JSON relevant indices may be out of order; the historical parser sorts them)
* 3,456 decisions, 432 window effects and 24 publisher effects independently matched
* Frozen E3 input SHA-256 in audit/metadata: `84c02a30c6f077d1c2d0e645be480616e66d93dd61ca5d660acb77bed37216b3`

| Model | E3 NF4–BF16 effect (pp) | Two-sided exact p | Exploratory Holm-3 p | Publisher signs | Leave-one-publisher-out range (pp) |
|---|---:|---:|---:|---|---|
| Qwen2.5-3B | 18.6745 | 0.0078125 | 0.0234375 | 8 + / 0 − | 17.119 to 20.194 |
| Llama-3.2-3B | 5.2664 | 0.046875 | 0.09375 | 6 + / 1 − / 1 zero | 4.063 to 6.217 |
| Mistral-7B | 1.9459 | 0.203125 | 0.203125 | 4 + / 4 − | 1.305 to 2.762 |

All p-values are exploratory. Publisher-sign-flip tests assume an appropriate exchangeability/symmetry condition; the test is not assumption-free. Eight clusters sharply limit inference. Multiplicity is adjusted across three E3 models but not across E1/E2 or every exploratory analysis.

## Additional outcome: format compliance

The completed experiments include invalid outputs: Qwen BF16 9, Qwen NF4 13, Llama BF16 0, Llama NF4 2, Mistral BF16 0, Mistral NF4 0. The frozen Arm A parser treats invalid responses as no selection when calculating the example-index statistic. Explicitly disclose this and add an alternative valid-only sensitivity analysis before finalizing the manuscript.

## Interpretation

E3 validates a model-specific interaction on previously unused *reports*, with eight publishers (Bitdefender unavailable) and one interior window per report. It is a retrospective, same-archive holdout, not an independent-corpus or temporal out-of-distribution study. Qwen exhibits a strong, directional interaction; Llama and Mistral are weaker in E3. Do not equate the E3 effect with relevance accuracy or infer that a difference between historical and E3 effect sizes is statistically meaningful without a direct comparison on a common publisher set.

## Reproducibility boundaries

This ZIP includes all 3,456 result checkpoint records and model run metadata, but does **not** include the private 72-window source text file, `GATE.json`, or the original 10.69 GB archive. The matching input digest is in checkpoints and E3 audit reports. Full prompt reconstruction and independent source-selection certification need the separately preserved frozen input and gate. Some checkpoint `raw` fields contain model outputs but not source report paragraphs. Review redistribution permissions and metadata before public release.

## Recommendation

E3 is computationally reproduced; keep it in the research manuscript as an exploratory same-archive holdout with explicit 8-publisher allocation. Next priority: an invalid-output sensitivity audit and a final source-provenance pack, then choose whether E4 is needed for wider quantization claims.
