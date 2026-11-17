# Results and statistical reporting guide

Each number in these tables is a percentage-point effect (not an absolute probability, accuracy or risk score). The electronic tables and Python scripts in `extensions/E5_synthesis` are authoritative for exact values and replay. Rounded entries below are presentation views.

## Original study: example-digit dependence interaction (NF4−BF16)

| Model | Free JSON Arm A | Constrained Arm B | Scored singleton Arm C |
|---|---:|---:|---:|
| Qwen2.5-3B | +11.36 | +11.42 | +0.30 |
| Llama-3.2-3B | +4.97 | +7.16 | +6.94 |
| Mistral-7B | +6.01 | +4.85 | +2.48 |

## Extension results

| Study | Model | Effect | Exact exploratory p | Holm-adjusted p | Notes |
|---|---|---:|---:|---:|---|
| E1 (N1−N0 BF16/NF4 disagreement) | Qwen | −0.175 | 0.9570 | 1.000 | 130/144 matched windows |
| E1 | Llama | +2.474 | 0.3594 | 1.000 | 110/144; invalid-rule sensitivity reverses sign |
| E1 | Mistral | +2.170 | 0.3594 | 1.000 | 144/144 |
| E2 (greedy−scoring) | Qwen | +0.397 | 0.3594 | — | 97.40/98.61% agreement BF16/NF4 |
| E3 (NF4−BF16 D) | Qwen | +18.6745 | 0.0078125 | 0.0234375 | eight publishers, within same archive |
| E3 | Llama | +5.2664 | 0.046875 | 0.09375 | same archive |
| E3 | Mistral | +1.95 | 0.203125 | 0.203125 | same archive |
| E4 (FP4−NF4 D) | Qwen | +8.48 | 0.171875 | 0.34375 | 47/576 invalid FP4 outputs |
| E4 | Llama | +2.21 | 0.1953125 | 0.34375 | 0/576 invalid FP4 outputs |

The different outcomes should not be pooled into a single meta-analysis: they differ in estimand, inference regime and selection population. E3 is an overlapping-publisher but disjoint-report holdout; E4 reuses its windows and is not an independent replication. E1's complete-case population is conditional on parse validity and differs by model.

## Invalid-output and selection rules

| Stage | Primary invalid treatment | Mandatory sensitivity/reporting |
|---|---|---|
| Historical A–C | Follow original frozen parser and definitions | Show schema failure and denominator |
| E1 | Four-cell complete valid windows for disagreement; failures counted unusable for F1 | Window→report→publisher; all-window invalid-as-empty; validity rates |
| E2 | Constrained singleton candidate validation | Candidate-choice agreement and ties |
| E3 | Historical Arm A-compatible rules | Invalid counts by model and format |
| E4 | Invalid modeled as empty selection for primary contrasts | Complete-case 53 Qwen / 70 Llama; format validity |

**Arm C denominator:** 6,912 prompt conditions, each assessed with eight continuations = 55,296 candidate scores; don't use 20,736 as the denominator of Arm C ties.
