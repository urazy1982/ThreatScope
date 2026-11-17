# Reproducibility levels and exact commands

## Level 0 — verify supplied files (no ML dependencies)

```bash
python3 verify_release_package.py
```

Recomputes SHA-256 on all files listed in the release manifest and detects unexpected additions. The manifest is generated after packaging and is not itself listed.

## Level 1 — historical Arms A–C CPU reanalysis

```bash
python3 reproduce/reproduce_all.py --out results_rerun
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

## Windows / WSL

Download a ZIP to `C:\Users\uraz\Downloads`; in WSL the input path is `/mnt/c/Users/uraz/Downloads/`. Extract into a fresh subfolder of `~/threat-study`. Copy *requested* status reports and final outputs to `H:\ThreatScope` (`/mnt/h/ThreatScope`). Avoid running experiments directly on mounted Windows paths; never overwrite original historical checkpoints.
