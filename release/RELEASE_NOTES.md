# ThreatScope v1.1.0 — Extension evidence release

**Title:** ThreatScope v1.1 — Precision, Prompt Invariance & Reproducible Evidence

This release preserves historical Arms A–C and adds four independently audited exploratory extensions: a neutral-example control (E1), greedy-versus-scored singleton robustness (E2), an eight-publisher within-archive report holdout (E3), and same-bit-width FP4/NF4 comparisons (E4). The full extension comprises 8,640 recorded model decisions. Its CPU replay and E3/E4 checkpoint verification pass.

**Principal finding:** Qwen's NF4−BF16 example-index sensitivity interaction replicates on 72 previously unused interior report windows (+18.67 pp; eight-publisher exact p=0.0078125; Holm-3 p=0.0234375). E1 offers no reliable neutral-prompt stability mitigation, E2 is a decoder robustness check (not a mechanism test), and E4's positive FP4−NF4 differences are inconclusive. Human-label limitations and within-archive dependence remain.

**Reproduce:** `python3 verify_release_package.py` and `python3 verify_e6.py`. Read `release/REPRODUCIBILITY_LEVELS.md`, `release/SCIENTIFIC_DISCUSSION.md` and `release/RELEASE_CHECKLIST.md` first. Historical per-experiment inference depends on source data and pinned GPU assets omitted from the public release.

**Data safety:** model output records and identifiers are included, full CTI source report texts and the 10.69 GB source archive are not. Rights review is required before making the ZIP public.

This is an archival research artifact, not a claim of manuscript acceptance or a validated cybersecurity deployment product.

## Final v1.1.0 additions (16 November 2026)

- `verification/`: independent standard-library recomputation of every E1–E4 number in the manuscript
  (`recompute_extensions.py`) and its output for this release; it matches the manuscript values exactly
  and agrees with the recorded validity of all 4,608 raw E3/E4 outputs.
- README and CITATION.cff name the companion manuscript, prepared for submission to *Applied Artificial
  Intelligence*.
- E2 publisher signs, counted with a 1e-9 tie tolerance, are 5 positive, 2 negative, 2 tied (the exact p-value is unchanged).
- Privacy check before release: no sentence from the private annotation sheets occurs in any released file.
