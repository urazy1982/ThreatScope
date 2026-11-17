# ThreatScope: integrated scientific discussion, v1.1.0

**Evidence status:** historical Arms A–C and extensions E1–E4 were completed on the author's GPU. The release provides archived decisions, historical code, E3/E4 raw output checkpoints, CPU statistical replay and source hashes. The E5/E6 verification is a replay and structural audit—not independent re-execution of inference. The following interpretations are limited to these records.

## 1. Research question and conceptual distinction

The study asks whether a *semantically irrelevant example digit* can become an unintended influence on structured selection decisions, and whether that influence interacts with model numerical precision. A user may provide an illustrative JSON list such as `{"relevant":[k]}` merely to define the output format; the answer should be determined by the target sentences. If the index `k` changes while all target sentences and the rest of the prompt remain fixed, any systematic difference in the selections reflects example-index dependence rather than a change in the underlying CTI question.

The original estimand is an equal-publisher, equal-report difference between NF4 and BF16 in the dependence statistic D defined in the manuscript, based on paired variations of the index in eight-sentence windows. It is **not** the raw percentage of outputs that differ, a causal mediation estimate, or an accuracy metric. Report- and publisher-level clustering is essential because eight index prompts share a window and multiple windows may share a report and publisher.

Avoid conflating four properties: (i) schema compliance—whether a JSON response can be parsed as a valid set of indices; (ii) example-index dependence—whether a shown example digit affects the decision; (iii) cross-precision stability—whether BF16 and a four-bit format give the same selections under a fixed prompt; (iv) relevance correctness—whether the selected sentences are useful CTI according to a credible reference. These are different outcomes and may move in different directions.

## 2. Historical result: a controlled interaction, not a universal low-bit effect

In the original nine-publisher Arm A free-generation experiment, the NF4–BF16 dependence interactions were +11.36 pp for Qwen2.5-3B, +4.97 pp for Llama-3.2-3B, and +6.01 pp for Mistral-7B. These estimates survived the historical Holm-3 family. Replacing unconstrained JSON generation with the grammar-constrained 256-subset output space (Arm B) did not eliminate the phenomenon: the corresponding estimates were +11.42, +7.16 and +4.85 pp. Thus output-schema restriction alone did not neutralize the example-digit association in the tested conditions.

Arm C restricted the model to a single choice and replaced free/constrained generation with candidate likelihood scoring, while also changing the instruction to request exactly one answer. Its Qwen interaction attenuated to +0.30 pp. The study does **not** identify which of the simultaneously changed factors is responsible. Moreover, significance differences across arms do not prove a difference between effects, and a nonsignificant estimate is not proof of equivalence.

The substantive contribution is a *precision-by-irrelevant-example interaction*, measured under matched text interventions and compared across decoding regimes. It does not establish that NF4 is systematically less accurate, unsafe, or operationally worse.

## 3. E1: an index-free demonstration is not a validated stability mitigation

E1 tests two prompts with no numerical index demonstration: N0 supplies the base instruction without an output example, while N1 adds the index-free JSON example `{"relevant":[]}`. It is necessarily a **different estimand**: the difference (N1 minus N0) in BF16/NF4 sentence-selection disagreement for the same windows, not D's dependence on a shown digit. This makes E1 useful as an intervention audit, but its result cannot be plotted as another Arm A–C example-digit effect.

All 1,728 generated records are present; 1,675 were parser-valid and 53 invalid. The frozen E1 primary analysis retains only windows for which all four model–precision–prompt cells are valid, and averages eligible windows within publishers: Qwen −0.175 pp on 130/144 matched windows, Llama +2.474 pp on 110/144, Mistral +2.170 pp on 144/144. No model has a compelling multiplicity-adjusted decrease in cross-precision disagreement.

This conclusion requires a missing-output qualification. For Llama BF16, N0 yielded 33/144 invalid responses whereas N1 had zero. When invalid results are instead treated as empty selections, the independently supplied sensitivity calculation reverses Llama's disagreement contrast to roughly −4.43 pp (exploratory p≈0.16); report-equal aggregation also changes the estimate. The frozen complete-case analysis remains primary because it was specified before seeing E1 outcomes, **not** because dropping malformed windows is unbiased. Display alternative estimands rather than choosing a new primary after observing the sign reversal.

N1 therefore has a notable *format-compliance* association for Llama BF16 in this context, while it has no demonstrated universal stability benefit. Empty outputs, malformed outputs and usable nonempty selections must remain distinct. Even apparent improved agreement could be achieved by selecting nothing and should not be sold as an operational improvement without relevance data.

## 4. E2: robustness of singleton extraction, not mechanistic identification

E2 compares constrained greedy decoding with whole-candidate likelihood scoring under the historical Arm C exact-one instruction and the same eight JSON singleton candidates. The two procedures agree on 97.40% of BF16 and 98.61% of NF4 prompts. For Qwen the NF4−BF16 example-index interaction is +0.298 pp under scoring and +0.694 pp under greedy; the +0.397 pp procedure contrast has an exploratory exact p=0.3594. With floating-point tolerance the publisher directions are 5 positive, 2 negative and 2 ties.

This high agreement is unsurprising: for Qwen the candidate strings share the same token prefix and differ mainly in the digit; selecting the most likely digit and scoring the whole singleton continuation should nearly coincide because subsequent closing tokens add little discrimination. E2 excludes a narrow artifact of using a whole-candidate score as the sole explanation for Arm C, but **does not** isolate the roles of the exact-one instruction, single-choice cardinality or candidate-set restriction. Those require unrun crossed cells; no mechanism is established by this release.

## 5. E3: retrospective report-level holdout in the same archive

E3 revisits the Arm A task on 72 previously unused reports, one interior eight-sentence window per report, from eight publishers. Allocation is 10 Securelist, 10 Trend Micro, 9 Unit 42, 9 Talos, 7 Group-IB, 9 Volexity, 9 SentinelLabs and 9 ASEC; Bitdefender had no unused eligible source reports. Selection excluded overlapping historical paths/content and selected-window target sentences, and used an explicit 5-word Jaccard near-duplicate heuristic. The gate was amended to test sentence overlap at the **candidate-window** rather than entire-report level before E3 inference, after an overrestrictive earlier rule caused insufficient coverage. This sequence should be disclosed as posthoc development rather than externally preregistered selection.

The 3,456 inference records reproduce NF4−BF16 example-digit interactions of +18.67 pp (Qwen), +5.27 pp (Llama) and +1.95 pp (Mistral). Across eight publishers, the exploratory exact two-sided p-values are 0.0078125, 0.046875 and 0.203125, with Holm-3 values 0.0234375, 0.09375 and 0.203125. The Qwen effect is positive across all eight publishers and remains positive in leave-one-publisher-out checks. The other two models do not meet the chosen multiplicity-adjusted criterion.

This is the most important external-validity extension, but **within archive only**. Publishers overlap with the original sample; report sources, editorial practice and collection date may also be correlated. Report-level disjointness and a near-duplicate filter do not establish temporal, semantic or truly independent-corpus isolation. The increase from historical Qwen +11.36 pp to E3 +18.67 pp is descriptive across two differently sampled populations, not a direct randomized comparison or evidence of a changing risk over time.

The package withholds original report text, original 10.69 GB archive and the separate private E3 input/gate file. Hence the released checkpoint hashes and decision records support statistical replay but not complete independent source-to-checkpoint attestation using only the public ZIP. A private provenance bundle should be retained by the author.

## 6. E4: same nominal bit-width does not imply identical behavior

E4 holds the E3 windows, two model families and bitsandbytes framework fixed while comparing FP4 with NF4, both nominal four-bit formats. The FP4−NF4 example-digit interactions are +8.48 pp (Qwen) and +2.21 pp (Llama), with exploratory exact p=0.1719 and 0.1953; Holm-2 is 0.3438 for each. In contrast with claims of an intrinsic four-bit effect, these observations suggest that representation details **may** matter, but the two format contrasts are statistically inconclusive here. They do not establish that FP4 is intrinsically riskier or less accurate.

Qwen FP4 had 47 invalid JSON responses among 576 generations (8.16%); Llama FP4 had zero. Under a complete-valid-window sensitivity analysis (all three precisions, eight prompt digits), FP4−NF4 estimates become +8.70 pp for Qwen on 53/72 windows and +1.76 pp for Llama on 70/72, again inconclusive. The primary analysis treats invalid outputs as empty according to the frozen E4 rule, which combines output compliance and selection behavior. Therefore malformed-response rates must accompany all reported dependence effects. FP4 and NF4 may also differ in numerical kernels and block scaling despite sharing nominal bit-width.

## 7. Statistical inference and evidence strength

Publisher-equal means provide a defensible balance across the nine historical or eight E3/E4 vendor categories, but few clusters limit statistical resolution. The exhaustive publisher sign-flip test is exact *conditional on its sign-exchangeability/symmetry assumptions*, not assumption-free. Tied publisher effects should be handled with a declared numerical tolerance; E2's raw float-based sign count overstated positives without changing its p-value. Holm adjustments must be stated with their family: three historical models within an arm, three E3 models, and two E4 formats/models as specified. Exploratory extensions are not independent confirmatory preregistrations just because local hashes were frozen.

Confidence intervals from hierarchical publisher/report bootstrap are descriptive at this sample size; they do not make claims of population coverage robust to unmeasured vendor dependence. Where pooled F1 is reported next to publisher-equal tests, the quantities must be named separately. Avoid using nonsignificant findings to support equivalence, or making new cross-arm causal claims from side-by-side p-values.

## 8. Human and AI relevance labels

The source archive contains 288 initially human-annotated slots, with Cohen's κ around 0.41 and marked adjudication asymmetry (91 of 100 disputed items resolved to H1's original label, five to H2). Fifteen items remained undecidable. The original 288 slots—not the 371 target slots created through duplicate-text propagation—are the correct primary reference population. The human assessments were made without surrounding report context, and the adjudications are not an unquestioned gold standard. Expanded slot-propagation analyses must be clearly labeled supplementary.

The Fable-generated 1,152 sentence labels are **AI annotations** and not human ground truth. Agreement with another model would show inter-model consistency, not expert validation. The study does not demonstrate improved CTI operational decisions or security outcomes; it demonstrates controlled selection instability and offers bounded, imperfect relevance-reference analyses.

## 9. Alternative explanations and generalization limits

The exposed interactions could reflect model-family particulars, output-template priors, training exposure to schema examples, quantization numerical error, decoding-induced threshold effects, report-position bias, publisher writing styles or tokenizer boundaries. The one-digit prompt variation is a tight textual control and historical token-ID checking supports that, but the experiment does not identify the internal causal pathway through the weights. The original windows were opening/closing positions; E3 addresses interior positions in new reports, yet does not vary languages, independent corpora, larger model families or deployment pipelines.

The forced singleton effect for Qwen could arise from output cardinality, instruction semantics or a mixture. A clean 2×2 instruction-by-cardinality design remains the next *optional* mechanistic experiment, not a prerequisite to describe the existing results accurately. It must use matched decoder choices so that instruction and cardinality are not again confounded.

## 10. Overall contribution and cautious conclusion

ThreatScope demonstrates a reproducible within-model sensitivity interaction: reducing weight precision from BF16 to NF4 can change the degree to which a semantically irrelevant JSON example digit influences selections, with substantial variation across model families and output procedures. The effect persists for Qwen on previously unused interior report windows from the same archive. E1 shows that index-free examples do not provide a universal stability mitigation; E2 confirms that the singleton scoring result is not tied to a specific output-extraction procedure; E4 shows suggestive but inconclusive additional format dependence. The evidence motivates **auditing structured LLM selectors for prompt invariance and parse validity under their actual deployment precision**, not declaring that one format is universally unsafe or that a defense is proven.

This release is suitable as a transparent empirical research artifact, conditional on source/annotation rights and final manuscript cross-checks. It is not a certified security product, model-risk standard or evidence of CTI deployment benefit.
