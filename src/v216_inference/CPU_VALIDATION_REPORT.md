# ThreatStudy v2.0.2 — independently executed CPU validation report

Execution environment: sandboxed Linux CPU host, Python 3.11+, no NVIDIA GPU, external source-data download restricted. **Date: 2026-11-13.**

## Scope and controls

- Original release `/mnt/data/ThreatStudy_CrossCorpus_v2_0_CPU_Gated.zip` kept unchanged. A separately versioned **CPU-only** copy is included here.
- Real existing evidence: `ThreatStudy_v151_Analysis_Results.zip` and `CTINexus_provenance_audit.json`, both uploaded by the user and embedded for exact reproducible derived-data audit.
- Model outputs in `scripts/cpu_replay.py` are **synthetically scripted** and do not constitute scientific confirmation.
- The genuine CTINexus article JSON files, CTI-Crawler report HTML/PDFs, and pinned HF tokenizers/checkpoints are **not available** on this CPU host. Authentic external-source label verification, real-corpus window selection, full token preflight, and actual inference are NOT complete.

## Executed verification

1. v2.0 original release integrity: **PASS (15 hashed files)**.
2. Original v2.0 unit suite: **12/12 PASS**.
3. Original v2.0 complete synthetic 80-report, 160-window, 10-source, 3-model, 2-precision, 8-example replay: **7,680/7,680 PASS**.
4. v2.0.2 extended unit/integration suite: **37/37 PASS** (12 original plus 25 additional tests).
5. v2.0.2 full synthetic replay: **7,680/7,680 PASS**, stored checkpoint hash tamper rejected.
6. Real v1.5.1 derived analysis: **six CSV hash checks PASS, 3,408 rows checked, 12 arm totals reconciled, 20 invalid outputs, 289 imported, 1 direct singleton-copy switch; three 5-source exact p values reproduce 0.0625 (Holm = 0.1875).**
7. CTINexus original user audit: **298 files, 148 unique texts, 147 doubletons and one quadruple; 0 publisher labels; annotation, demo, test are not independent report populations.**
8. Statistical simulation: **six normal-publisher standardized-effect cases, 4,000 draws each, exact 1,024 sign-flip configurations per draw**; diagnostic only.
9. All Python module syntax checks, shell syntax check, and clean-extraction release check to be recorded in the final machine output.

## Engineering defect found and corrected

The original `prepare()` deduplicated by `sha256([publisher,text])`: if an identical article appeared under two different publisher labels, the different IDs let it pass. v2.0.2 rejects duplicate report texts even when publishers differ (after whitespace normalization and case folding). This is essential to avoid treating syndicated or mislabeled copies as independent sources. It does not detect paraphrased or near-duplicate articles; these still require a separate content-similarity and human provenance audit.

v2.0.2 also fails closed at both the shell GPU entry point and the model runner before importing CUDA libraries. It is deliberately **not GPU-ready**, because it has not authenticated any actual publisher-labeled external corpus. Do not bypass this control by editing the release.

## Scientific methodological warning

The balanced eight-example statistic is algebraically zero under an index-invariant response set. However, a model that chooses the **first k+1 indices under example k** (using the example index as a cardinality cue rather than literally copying the singleton example) produces a positive statistic. Therefore a positive score does **not** uniquely establish direct answer copying. Report selection cardinality, position exposure, validity, and direct singleton switching separately; consider a matched-cardinality, positive-vs-negative-control arm before mechanistic claims.

## Ten-publisher inferential sensitivity (synthetic normal source-effects only)

Results in `evidence/source_power_simulation.json`; the `delta_over_publisher_sd=1.0` scenario gives a conservative three-model significance probability of 0.5763 under this **hypothetical** model (4,000 draws, 10 independent normally distributed source effects). No empirical variance or effect distribution was estimated from external CTI documents; these numbers must not be presented as experimental power based on pilot estimates.

## Next required scientific gates (not executed)

1. Obtain original source-documented collection itself; the `peng-gao-lab/cti-crawler` GitHub code repo does **not** contain the report archive. The released APT set is described at https://huggingface.co/datasets/CZLi/apt-reports (source metadata and files require independent inspection); the larger CTI set is linked from the original GitHub README via Google Drive.
2. Authenticate original per-article URL and publisher mapping; prevent cross-source exact/near duplicates, overlap with prior SMAH corpus, and missing or shell/boilerplate-only articles.
3. Re-freeze source names, corpus SHA, selection algorithm, sample sizes and prompt/statistical protocol after **actual** eligible publisher counts are known. v2.0.2's existing CTINexus publisher list cannot be silently repurposed for the crawler corpus.
4. Run model-pinned real-tokenizer parity and context gates on the real frozen text and release the **newly verified GPU protocol** before any RTX 5090 work.

**Conclusion:** All tests feasible with the currently present code, simulated data, and uploaded derived evidence have been executed. The outstanding work is external dataset acquisition and authentication, which cannot be truthfully replaced with synthetic CPU fixtures.
