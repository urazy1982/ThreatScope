# ThreatScope — Manuscript revision insertions (author-editable)

**Working title:** ThreatScope: Quantization-Dependent Example-Index Sensitivity in Cyber-Threat Intelligence Selection. Keep the historical study's exact terminology and mathematical definition of the dependence statistic D. These are additions to draft v0.12, **not a replacement for the full manuscript**.

## Revised abstract addendum (integrate, do not paste independently)

After the original nine-publisher crossed experiment, we performed exploratory controls evaluating index-free prompts, singleton decoding, report-level holdout validation, and an alternative four-bit format. A 72-report, eight-publisher retrospective holdout from the same source archive reproduced the positive NF4–BF16 dependence interaction for Qwen2.5-3B (+18.67 percentage points; exact p=0.0078; Holm-adjusted p=0.0234), but not family-wise significant effects for Llama or Mistral. Neutral-format examples did not consistently improve precision agreement; greedy singleton decoding closely matched the original likelihood scorer; and FP4–NF4 interactions were positive but inconclusive. These findings delimit deployment-sensitive behavior rather than demonstrating improved relevance accuracy or a mechanism for Arm C attenuation.

## Extension methodology (after Arms A–C)

All four extensions were developed after inspection of the historical outcomes and must be identified as **exploratory posthoc** investigations. The original Arm A–C estimand is the NF4–BF16 difference in dependence of selection on a semantically irrelevant shown index. E1 instead measures between-precision selection disagreement under N0 (no example) and N1 (an index-free JSON example), not dependence on an example digit. E2 holds the exact-one instruction, eight canonical singleton candidate outputs, and model constant while comparing constrained greedy decoding with the historical candidate likelihood scorer. E3 draws 72 previously unused reports from the same historical APT archive, selects one eight-sentence interior window per report, and excludes direct historical report/path/content and selected-window sentence overlap; Bitdefender contributes no unseen reports. The selection was amended before E3 inference after an earlier whole-report sentence-overlap rule disproportionately excluded otherwise eligible windows. E4 reuses E3's same windows and quantization stack with FP4, permitting nominally matched four-bit format comparisons in Qwen and Llama. The analyses retain publisher-equal estimands and distinguish inferential sign-flip assumptions, report clustering, valid-response handling, and planned multiplicity families.

## E1 — Neutral example control

Across 1,728 completed responses, 1,675 were schema-valid and 53 malformed. Under the internally frozen complete-case rule, the publisher-equal N1–N0 changes in cross-precision disagreement were −0.18 pp (Qwen), +2.47 pp (Llama), and +2.17 pp (Mistral), none statistically persuasive after correction. The complete-case restriction left 130, 110, and 144 of 144 matched windows respectively. Report-equal and invalid-as-empty sensitivity analyses must be shown separately; in particular, the Llama contrast reverses sign under the invalid-as-empty rule (approximately −4.43 pp, according to a separate independent sensitivity calculation), so the result is not stable to missing-output treatment. Llama BF16 schema validity increased from 111/144 under N0 to 144/144 under N1, but this does not establish better CTI selection accuracy. Distinguish format compliance from stability and relevance.

## E2 — Singleton decoding robustness

Constrained greedy choice and the frozen whole-candidate likelihood scorer produced identical singleton indices in 97.40% (BF16) and 98.61% (NF4) of the 2,304 matched prompts. Qwen's NF4–BF16 dependence interaction was +0.298 pp under scoring and +0.694 pp under greedy, a +0.397 pp difference (exploratory exact p=0.3594). The candidate strings differ only by the shown one-digit index, and share almost all their tokens. This is a procedural robustness check **not** an identification of the cause of historical Arm C attenuation. With floating-point tolerance, publisher effect signs are 5 positive, 2 negative, 2 tied.

## E3 — Previously unused report holdout

The eight-publisher retrospective holdout included 72 previously unused reports with one interior eight-sentence window per report: 10 Securelist, 10 Trend Micro, 9 Unit 42, 9 Talos, 7 Group-IB, 9 Volexity, 9 SentinelLabs, and 9 ASEC. Original Bitdefender had no unused eligible reports. The 3,456 new inferences reproduced a Qwen NF4−BF16 dependence interaction of +18.67 pp (exact p=0.0078125; Holm-3 p=0.0234375). Llama's +5.27 pp (Holm p=0.09375) and Mistral's +1.95 pp (Holm p=0.203125) do not pass this family-wise threshold. The holdout does not establish independence of archive, publisher, time or collection process; near-duplicate exclusion is heuristic and does not guarantee semantic independence.

## E4 — Four-bit format comparison

On the exact E3 windows, FP4−NF4 dependence interactions were +8.48 pp for Qwen and +2.21 pp for Llama. Publisher-level exact exploratory p-values were 0.1719 and 0.1953 (both Holm-adjusted 0.3438), leaving both format contrasts inconclusive. Qwen FP4 produced 47 malformed responses of 576 (8.16%); Llama FP4 produced none. Under complete fully valid eight-index windows, FP4−NF4 was +8.70 pp over 53 Qwen windows and +1.76 pp over 70 Llama windows. These results measure model- and deployment-specific decision sensitivity; they do not establish that FP4 is intrinsically less safe or less accurate than NF4.

## Discussion and limitations paragraph

The study's strongest reproducible evidence concerns numerical-example dependence and its interaction with the model's precision or four-bit representation. It does not validate a causal mediating mechanism for the original Arm C attenuation, because exact-one instruction and permissible output cardinality remain crossed incompletely. Human relevance judgments show only moderate initial agreement and asymmetric adjudication; the original 288 judged slots should be the primary sample and duplicate-propagated labels should be supplementary. E1 invalid-output handling materially affects the Llama point estimate, and publisher-level exact sign flips require sign-exchangeability or symmetry assumptions. E3 broadens report positions and report identities but uses the same parent source archive and partly the same publishers. The E4 quantization-format comparison is exploratory, and differences in outputs are not an estimate of practical cybersecurity consequences without stronger independent correctness judgments.

## Mandatory manuscript housekeeping

* Original manuscript Arm C's single score tie is one among **6,912 prompt conditions** with **55,296 scored candidate continuations**, not one among 20,736 Arm C prompts.
* Replace wording like “effect disappeared” with “effect attenuated to near zero” when tests are nonsignificant.
* Fix pagination and appendix page totals.
* Preserve v2.1.6/v2.2.1 chronology, absence of verified external preregistration, model revisions and source hashes, and posthoc status of all new extensions.
* No journal acceptance or reviewer sign-off has been established by these experiments.
