# Reproducibility levels and exact commands

## What a reader can reproduce independently

This summarises Table 2 of the manuscript.

| Question | Answer | How / what limits it |
|---|---|---|
| 1. Recalculate the published statistics from released decisions? | **Yes**, on a CPU, standard library | `reproduce/reproduce_all.py` (Arms A–C), `verification/recompute_extensions.py` (E1–E4), `annotation/analyze_original_slots.py` and `annotation/analyze_ai_labels.py` (label-based analyses; agreement statistics and the E1 human-reference F1 also reproduce from the released slot labels). Building slot labels from the annotators' sheets is author-side. |
| 2. Reconstruct the exact input windows from the source collection? | Main study and annotated subset: **yes**. E3: **partly** | Pinned `CZLi/apt-reports` revision, deterministic hash-checked preparation (`src/v216_inference`), per-sentence SHA-256 in `data/prepared/inputs_redacted.jsonl`, `reproduce/restore_reference_archive.py`, `annotation/human_labels/draw_windows.csv`. For E3 the report/window identifiers, start positions and per-call input hashes allow a rebuilt input to be verified, but no released script extracts the E3 windows. |
| 3. Rerun inference with pinned weights and software? | **Yes**, not guaranteed bitwise identical | Pinned model revisions, library/CUDA versions and GPU in `ENVIRONMENT.md` and `data/config/study.json`. Needs the input text and licensed weights; outputs may differ on other hardware or library versions. The frozen Arms B/C runner authorises GPU runs only with the author's original input archive (on request, non-commercial research). E3/E4 reruns need the private E3 input. |
| 4. Reproduce the complete data-selection procedure, including E3? | Main study and planned subset: **yes**. Annotated draw and E3: **no** | Main-study selection is deterministic; `annotation/select_subset.py` regenerates the planned subset. The annotated draw's ranking key was not preserved (its membership is released and verified). The E3 selection gate (code and provenance report) is not distributed, so only its outcome can be checked. |

## Level 0 — verify supplied files (no ML dependencies)

```bash
python3 verify_release_package.py
```

Recomputes SHA-256 on all files listed in the release manifest and detects unexpected additions. The manifest is generated after packaging and is not itself listed.

## Level 1 — historical Arms A–C CPU reanalysis

```bash
python3 reproduce/reproduce_all.py --out results_rerun
```

Human-label analyses on the 288 original annotation slots (about 20 s):

```bash
python3 annotation/analyze_original_slots.py
```

This is computational reanalysis from archived records, not independent generation. Run in a clean working directory or choose a unique `--out`; no CUDA needed. The historical scripts have their own frozen hash checks.

## Level 2 — full extension replay

```bash
python3 verify_e6.py
```

Expected last line: `THREATSCOPE_E6_CPU_AUDIT_PASS`. E1/E2 exported decisions and E3/E4 checkpoint bodies are checked with their respective limits. E1/E2 raw checkpoint bodies were not present at E6 assembly time.

## Level 3 — scientific sensitivity analyses

Inspect and execute scripts under `extensions/independent_audits/` and `extensions/E5_synthesis/verify_e5.py`. Their output should be kept separate from the historical confirmatory tables. Consult `release/RESULTS_INTERPRETATION.md` for estimands and invalid-output rules.

## Level 4 — full inference (requires authorized source text and pinned GPU setup)

Use the original inference folders and per-experiment READMEs, not a single generic cross-experiment command. Requires the CTI source collection, private E3 selected-window input and holdout manifest, pinned tokenizers and model weights, GPU/CUDA matching the stated lock, and rights to access the source publications. Do **not** substitute new source windows while claiming byte-identical reproduction.

Exact source-to-prediction checks for E3 require private `inputs_E3_private.jsonl` SHA-256 `84c02a30c6f077d1c2d0e645be480616e66d93dd61ca5d660acb77bed37216b3`. The 10.69 GB APT distribution ZIP and human raw annotation workbooks are intentionally omitted. Original experiment revisions and archive paths should be verified against the author's local manifests, not guessed.

## Running on Windows (WSL)

Extract the release into a fresh folder on the Linux file system (for example under `~/`), not on a mounted Windows drive, and write outputs to a new folder such as `results_rerun/`. Never overwrite the released checkpoints or results.
