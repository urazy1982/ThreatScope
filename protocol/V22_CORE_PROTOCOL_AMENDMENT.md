# ThreatStudy v2.2-Core — Short-cycle amendment (DRAFT, NOT FROZEN)

**Title:** One Digit, Different Decisions: Quantization-Dependent Example Sensitivity in Structured Cyber-Threat Intelligence Relevance Selection

## Inherited data and evidence

- APT corpus: nine publishers, eight reports per publisher, 144 eight-sentence windows, 1,152 sentence slots; content fingerprint `461682f329a5cca95715d6d7a12356dddb3f38f3adf0e221a2443bdecfdd354e`.
- Three pinned models and BF16/NF4 contrast from archived v2.1.6 `config/study.json`; unchanged eight example-index prompts `example_0` through `example_7`.
- v2.1.6 Arm A results are retained as **historical empirical evidence**, not relabeled as v2.2 results.

## Arm B (schema-constrained, 6,912 new outputs)

The original task instruction and user prompt are unchanged. Generation is constrained to **one of 256 canonical JSON strings** `{"relevant":[...]}`, each representing a unique subset of 0–7 in ascending order. Empty set is allowed. The exact 256 strings are enumerated in `v22core/constraints.py`.

This constrains both JSON validity and output formatting to a strict canonical language, **not just JSON schema validity**. It is a change to decoding and may influence semantics. Before inference, tokenizer-specific output encodings must round-trip exactly, all 256 subsets must be reachable via token-prefix constraints, and 0 parser rejects must occur. Output token cap remains 96; if any authorized output cannot complete within that cap, pause and amend rather than silently increasing it.

## Arm C (single choice by candidate likelihood, 6,912 new score vectors)

The eight original example-index prompts are unchanged. The new system instruction is the exact `SYS_SINGLE` string in `v22core/core.py`, whose hash must be frozen before inference; it requires exactly one selected index even when nothing meets the ordinary relevance threshold. This is a **forced-choice task** (a change in instruction as well as cardinality), so it does not by itself identify mediation by selection-set size.

For each prompt, score eight canonical candidate continuations `{"relevant":[j]}` for j=0–7 plus the model's verified end-of-turn token; sum conditional token log-probabilities without length normalization. The winner is the candidate with the highest summed score, with exact ties assigned to the lowest index. Record all eight scores, candidate token lengths, softmax-normalized candidate mass, end-of-turn ID, model identity, and context tokens. `v22core/scoring.py` implements and CPU-tests the batched scoring kernel. A tokenizer gate compares the full assistant-turn chat template with prefix + candidate + end-of-turn token exactly.

## Before actual v2.2 inference

1. Freeze hashes for protocol, all source modules, CUDA environment, model/tokenizer revisions and new Arm B grammar implementation. Register the time-stamped protocol before seeing B/C outcomes (OSF, if required by the selected journal).
2. Run the CPU tokenizer/template preflight on Ubuntu-Qua using `v22core.tokenizer_gate` with the frozen baseline archive and pinned revisions. Every index prompt must have equal input-token length for each window; all 256 JSON continuations must round-trip; all Arm C candidate chat templates must align exactly; any fail blocks GPU.
3. Replay the **frozen 432-call Arm A sample** generated in `results/v22_replication_manifest.json`. Record byte-level, decision-level and validity agreement separately. An imperfect replay triggers an explicit provenance/comparability discussion; it does **not** silently authorize reuse nor automatically trigger a 6,912-call rerun. Arms B and C can still be compared directly within their own model/precision pairs.
4. Begin **Arm C** to test fixed single-choice sensitivity, followed by **Arm B** to test canonical constrained JSON. Run every predeclared cell to completion; no outcome-dependent stopping.
5. Independently verify every v2.2 checkpoint, then recompute source-level exact two-sided sign-flip tests (2^9 assignments). Correct the three models within each new hypothesis by Holm. As a clearly labeled sensitivity, also report Holm across all six B/C model tests.
6. Freeze human gold labels in a **separate future phase**, only if two genuine blinded annotators are available. Until then, do not report gold-defined false-positive or relevance F1 claims.

## Fixed interpretation rules

- Positive effects in both B and C: source-supported sensitivity across two distinct output interventions; not proof of cardinality mediation.
- B positive, C weak/inconclusive: consistent with an effect sensitive to forced-choice scoring, not uniquely mediated by cardinality.
- B weak, C positive: new method-specific phenomenon; investigate; no broad mechanism assertion.
- Both weak/inconclusive: v2.1.6 Arm A remains a valid observed free-decoding result, with narrower generalization.

**Preregistration caveat:** This protocol is a drafted decision document, and no OSF submission has been made. The v2.1.6 data have already been seen. Label all archived-data diagnostics explicitly exploratory.
