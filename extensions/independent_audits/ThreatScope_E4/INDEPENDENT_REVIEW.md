# ThreatScope E4 — Independent CPU audit and scientific review

Source: user-uploaded `ThreatScope_E4_Complete_Results.zip`. This audit uses an independently authored standard-library script (`e4_independent_audit.py`), not the release's analysis script.

## Verification

- ZIP integrity: PASS; 1,183 entries.
- FP4 checkpoint files: 1,152/1,152; Qwen 576, Llama 576.
- Each checkpoint's raw hash, record hash, parser result and run-metadata identity digest: PASS.
- Checkpoint choices and hashes agree with 1,152 exported E4 text-free decision records: PASS.
- E3 historical reference decisions: 3,456 records; complete combined 4,608-cell grid over 72 unique windows: PASS.
- Six effects, sign-flip p-values, publisher sign counts, and two Holm-2 adjusted p-values independently reproduced.
- CUDA generation and checkpoint weight bytes are **not** independently reproduced on this CPU server.

## Main findings

| Model | NF4−BF16 (pp) | FP4−BF16 (pp) | FP4−NF4 (pp) | FP4−NF4 exact p | Holm-2 p |
|---|---:|---:|---:|---:|---:|
| Qwen2.5-3B | +18.6745 | +27.1567 | +8.4821 | 0.171875 | 0.343750 |
| Llama-3.2-3B | +5.2664 | +7.4787 | +2.2123 | 0.1953125 | 0.343750 |

The primary FP4−NF4 contrast is not statistically persuasive for either model. An insignificant contrast is not an equivalence finding. Positive FP4−BF16 effects are descriptive secondary results, with their reported unadjusted exploratory p-values (Qwen 0.0078125; Llama 0.0234375).

## Invalid-output and complete-case sensitivity

The original analysis treats invalid JSON as selecting nothing (historical Arm A rule). FP4 produced 47/576 invalid Qwen outputs (8.16%) and 0/576 invalid Llama outputs. Therefore invalid-output handling is scientifically material.

A stricter sensitivity analysis retained a window only if all eight anchors were valid under **BF16, NF4 and FP4**. This yielded:

| Model | Fully valid windows | FP4−NF4 (pp) | Exploratory exact p | FP4−BF16 (pp) |
|---|---:|---:|---:|---:|
| Qwen2.5-3B | 53/72 | +8.6961 | 0.1640625 | +28.0283 |
| Llama-3.2-3B | 70/72 | +1.7628 | 0.343750 | +7.5062 |

This analysis preserves the direction but not significance of the FP4−NF4 contrasts. Complete-case selection can itself induce bias; it is a sensitivity check, not a retrospective replacement of the primary rule.

## Provenance and interpretive boundaries

- E4 reuses the same E3 report windows. It is not a second independent test sample.
- Both FP4 and NF4 use the same nominal storage width, but differences also include model/kernel numerical behavior; format alone cannot be claimed as a proven isolated causal component.
- Only two model families and eight publisher groups are tested.
- The historical E3 reference decisions are available, but the full E3 checkpoint bodies, full frozen E3 source text and E3 gate were not included in this ZIP. Their independent provenance must be verified by the earlier E3 audit and archive.
- Report publisher-level sign flips require an exchangeability/symmetry assumption; descriptive estimates and p-values must not be overgeneralized.
- There is no new expert relevance-quality labeling on these E3 windows, so an extraction-quality improvement cannot be inferred from sensitivity changes.

**Recommendation:** E4 is complete at the decision-level reproducibility standard. Integrate it into the manuscript as an exploratory same-width quantization-format robustness test, and proceed to final E1–E4 synthesis without additional GPU work strictly required for E4.
