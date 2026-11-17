# ThreatScope-E4-FP4-v0.1 — Protocol amendment, before GPU runs

1. E4 originally envisaged AWQ/GPTQ as an alternative four-bit *implementation*. This release selects **bitsandbytes FP4** instead: a same-width format contrast against bitsandbytes NF4, with much better control of implementation and calibration. It is an exploratory post-E3 amendment and cannot claim an independent new holdout.
2. Primary model-specific estimand: equal-publisher average of `D_FP4 - D_NF4`, where D is the paper's example-digit association, averaged over each report's selected interior window. Two-sided exhaustive publisher-level sign-flip test over 2^8 sign configurations per model; Holm-2 across Qwen and Llama. CIs, if added, must be explicitly descriptive.
3. Secondary: `D_FP4 - D_BF16`, `D_NF4 - D_BF16`, publisher directions, invalid JSON rates, token-generation caps, selected cardinality. No unannotated claim of CTI relevance improvement.
4. Both model revisions are pinned in reference_config.json. Same 72-window input identity and Arm A prompt. No resampling after FP4 results are observed.
5. Limitations: only two model families; same source archive and E3 windows; FP4 and NF4 differ in quantization representation and possibly numerical kernels; exact sign flips require exchangeability; this does not test AWQ or GPTQ.
