# ThreatScope v1.1.0 — Reproducible Research Artifact

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24392692.svg)](https://doi.org/10.5281/zenodo.24392692)

**Archived at Zenodo:** https://doi.org/10.5281/zenodo.24392692 — data, results and documentation under [CC BY 4.0](LICENSE-DATA.md); code under the [MIT licence](LICENSE).

**Quantization-dependent example-index sensitivity in cyber-threat intelligence selection**

Companion release for the manuscript *One Digit, Different Decisions: Quantization-Dependent Prompt Sensitivity of Language Models in Cyber Threat Intelligence* (U. Yavanoğlu), prepared for submission to *Applied Artificial Intelligence* (Taylor & Francis). The manuscript is not yet published; cite this release by its Zenodo DOI (see [CITATION.cff](CITATION.cff)).

This repository release preserves the complete historical ThreatScope v1.0.0 research tree and adds E1–E4 experiments plus independently checked E5/E6 CPU reanalysis. Start with [release notes](release/RELEASE_NOTES.md), [scientific discussion](release/SCIENTIFIC_DISCUSSION.md), and [reproducibility levels](release/REPRODUCIBILITY_LEVELS.md). The [original v1.0.0 README](docs/historical_release_metadata/v1.0.0_README.md) is archived unchanged.

## Key scientific evidence

- Original Arm A (nine publishers): NF4−BF16 example-index interactions were Qwen **+11.36 pp**, Llama **+4.97 pp**, Mistral **+6.01 pp**.
- **E1:** index-free example intervention, 1,728 records; no significant improvement in cross-precision disagreement under the frozen complete-case rule; model-specific JSON validity change.
- **E2:** 2,304 Qwen singleton decisions; greedy and scored selection agree 97.40% (BF16) and 98.61% (NF4), but decoding robustness is not mechanism isolation.
- **E3:** 3,456 records on 72 previously unused interior report windows from **eight publishers within the same archive**; Qwen +18.67 pp (Holm-3 p=0.0234375).
- **E4:** 1,152 new FP4 decisions; FP4−NF4 interactions Qwen +8.48 pp, Llama +2.21 pp, both family-wise inconclusive.
- **Expert labels (288 original annotation slots):** Llama's F1 is lower under NF4 than BF16 in both multi-select arms (Arm A −0.071, exact p=0.0039), with every expert label set and slot set; the example effect touches relevant and irrelevant sentences alike.

This is a study of **prompt-index dependence**, not a demonstrated increase in threat-intelligence accuracy or operational risk. E1's disagreement estimand is different from the original Arms A–C effect. Extensions are exploratory/posthoc and are not external preregistrations.

## Independent recomputation for the manuscript

[`verification/`](verification/README.md) contains a standard-library script, written separately from the analysis code, that recomputes every E1–E4 number reported in the manuscript from the decision records and the raw E3/E4 outputs (`python3 verification/recompute_extensions.py`).

## Verify without GPU

Python 3.10+ (stdlib only):

```bash
python3 verify_release_package.py
python3 verify_e6.py
```

To reproduce historical statistics, use `python3 reproduce/reproduce_all.py --out results_rerun` (run in a working copy). The human-label analysis on the 288 original annotation slots is rerun with `python3 annotation/analyze_original_slots.py` (see [annotation/README.md](annotation/README.md)). Reports and discussion are in `release/`; experimental code in `src/` (historical) and `extensions/` (E1–E4). Decision evidence in `extensions/E5_synthesis/evidence/`, and available raw E3/E4 output checkpoints in `extensions/E3_checkpoints/` and `extensions/E4_checkpoints/`.

## Citation, data and disclosures

See [CITATION.cff](CITATION.cff), [DATA_STATEMENT.md](DATA_STATEMENT.md), [RELEASE_CHECKLIST](release/RELEASE_CHECKLIST.md) and [PRIVATE_ARTIFACTS_NOT_INCLUDED](release/PRIVATE_ARTIFACTS_NOT_INCLUDED.md). Original full publisher report text, selected E3 source windows, licensed model weights and some raw annotation evidence are **not bundled**. Review redistribution rights before publishing. Code and result licenses are recorded in `LICENSE` and `LICENSE-DATA.md`.

The released computational audit verifies archived data and statistics, **not** fresh model inference. What can and cannot be reproduced independently is summarised in [reproducibility levels](release/REPRODUCIBILITY_LEVELS.md).
