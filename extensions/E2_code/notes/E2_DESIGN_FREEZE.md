# ThreatScope E2 — prospective local protocol freeze, v0.1.0

This amendment is **after** the v2.1.6/v2.2.1 and E1 outcomes were seen. It is a targeted explanatory study, **not** prospective preregistration relative to those earlier results. Freeze code and data fingerprints before new E2 inference. Preserve the uploaded v1.0.0 results as historical records.

**Research question:** Does the drastic Qwen attenuation in Arm C persist when response space, prompt, system instructions and suffix formatting are held fixed but the decision procedure changes from teacher-forced joint suffix likelihood maximization to left-to-right greedy token selection constrained to the same eight candidate suffixes?

**Treatment:** decode/search mechanism (whole-candidate score argmax versus constrained greedy); same singleton JSON candidate grammar and EOT. The exact-one cardinality and instruction remain the same. This isolates one significant portion of the historical Arm C confound; do not describe it as establishing mediation of all differences between Arms A/B/C.

**Population:** exact original 144 windows × 8 example anchors × 3 model families × BF16/NF4. Stage-1 model: Qwen (the originally striking Arm C attenuation); pre-defined first analysis is 144-window complete Qwen BF16/NF4, 2,304 new generations, compared with 2,304 pre-existing historical Arm C scores. If necessary, repeat Llama/Mistral as supporting robustness, separately labeled.

**Primary per-window estimand:** the original diagonal example-index effect, `D=(T−C/8)/7` for eight anchors, where T is self-anchor selection count and C is total candidate selections. In exact-one candidate space, C=8, so D=(T−1)/7. Each publisher has 8 reports × 2 windows. Primary E2 contrast: publisher-equal average of `(D_NF4−D_BF16)_greedy − (D_NF4−D_BF16)_scoring`. Exact sign-flip across nine publishers is **exploratory**, requiring sign-exchangeability; 4,000-draw hierarchical publisher/report bootstrap CI is descriptive. Use consistent percent-point scale and report all nine publisher values.

**Secondary outcomes:** per-anchor exact greedy/scorer decision agreement, BF16 and NF4 separately; selection frequencies by example index; perfect format compliance required by fixed response grammar; equal candidate byte strings and tokenizer-aligned EOT verified before inference; call/checkpoint hashes and source revisions; no post-hoc subset dropping.

**Failure gates:** wrong dataset/config hashes; nonpinned model revision; drifted PyTorch/transformers/bitsandbytes; CPU offload; missing NF4 Linear4bit; non-identical candidate lengths; tokenizer suffix mismatch; noncanonical output; input/record/prompt/identity SHA-256 mismatch; GPU occupied by another compute process; missing any of the 8 anchors per window; incomplete 144-window primary cell. Fail closed and preserve partial checkpoint for diagnosis.

**Interpretation decision:** If constrained greedy remains near scoring Arm C, the single-choice output space/instruction may explain much of attenuation; if materially different while holding candidate space fixed, search/decoding is implicated. In neither case infer operational CTI correctness, universal behavior, or complete causal mediation without E3/external controls. An additional matched multi-select factorial is needed to separate cardinality and instruction effects.
