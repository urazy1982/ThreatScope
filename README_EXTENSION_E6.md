# ThreatScope — v1.1 extension / E6 scientific release

This is a **supplement** to historical v1.0.0. The original `src/`, `results/`, `annotation/`, and historical README are preserved. The new evidence is in `extensions/`. No historical results were changed.

## What is reproduced

* Historical Arms A–C: frozen historical release, 9 publishers, Qwen/Llama/Mistral, BF16 and NF4, 20,736 principal inference conditions.
* E1: no-output-example vs. index-free JSON example, 1,728 decisions; results are exploratory and use a different estimand from Arms A–C.
* E2: Qwen singleton constrained-greedy vs. teacher-forced likelihood, 2,304 decisions; procedural robustness, **not** instruction/cardinality causal identification.
* E3: 72 interior windows from unused reports in the **same** APT distribution ZIP; eight publishers (not Bitdefender), 3,456 decisions, retrospective holdout.
* E4: Qwen and Llama FP4 on those same E3 windows, 1,152 decisions, exploratory same-nominal-bit-width format comparison.

## Verification (CPU)

From this directory, run `python3 verify_e6.py` (Python 3.10+, no third-party dependencies). The `extensions/E5_synthesis/verify_e5.py` is rerun, and E3/E4 raw checkpoint counts and hashes are cross-checked. No GPU is required for statistical replay.

## Human annotations and privacy

The original v1.0.0 `annotation/` tree is preserved as an archived historical artifact. Do **not** interpret AI labels as expert labels or propagate 288 manually labeled slots into an enlarged independently annotated population. The 288 original annotation slots remain authoritative; historic 371-slot propagation is supplementary. Recheck publication permission before exposing the human annotation workbooks or publisher full texts.

`extensions/E3_checkpoints/` and `extensions/E4_checkpoints/` contain generated outputs and hashes, not source CTI report texts. E3 source-selection manifests and the actual 72-window text file remain outside this public package; exact source-to-checkpoint identity depends on those private artifacts. Before publishing, perform a licensing/privacy review of all included historic files.

## Scientific interpretation

See `extensions/E5_synthesis/SCIENTIFIC_SYNTHESIS.md`, `MANUSCRIPT_REVISION_INSERTIONS.md`, and `E6_READINESS_AUDIT.md`.

## Publication and authorship

This ZIP is prepared for GitHub; **it has not been uploaded or released automatically**. A release tag and repository URL must be confirmed after the user uploads it. Use an additive Git commit rather than rewriting the original v1.0.0 tag.
