# Protocol chronology and inferential families

| Stage | Data/procedure | Status and chronology | Primary quantity | Multiplicity |
|---|---|---|---|---|
| Historical A / v2.1.6 | 144 windows, 9 publishers; free JSON | Main historical frozen analysis | NF4–BF16 interaction in example-digit D | Holm across 3 models |
| Historical B / v2.2.1 | 256 valid subsets grammar | After Arm A outcomes, locally frozen amendment | Same D interaction | Holm across 3 models; separate exploratory B/C family |
| Historical C / v2.2.1 | Exact-one prompt plus candidate scoring | After Arm A outcomes, locally frozen amendment | Same D interaction | Holm across 3 models |
| E1 / v1.1.2 | N0 vs N1 index-free prompts, historical 144 windows | Exploratory; prompt version updated before E1 run | N1−N0 BF16/NF4 disagreement, four valid outputs | Holm across 3 models |
| E2 / v0.1.2 | Qwen, historical Arm C singleton candidates | Exploratory; runtime-format hotfixes | Greedy−scoring difference in D interaction | Exploratory, Qwen only |
| E3 / v0.4 | 72 unused reports, 8 publishers; interior windows | Retrospective, posthoc gate v0.3 frozen before inference | NF4–BF16 D interaction | Holm across 3 models |
| E4 / v0.1.1 | Qwen/Llama FP4 on E3 windows | Exploratory post-E3 protocol amendment | FP4−NF4 D interaction | Holm across 2 models |

**Key boundaries:** E1 is not D; E2 is not causal mediation; E3 is not independent-corpus or temporally held out; E4 is not an AWQ/GPTQ test. Exact publisher sign flips rely on sign exchangeability and bootstrap intervals are descriptive.
