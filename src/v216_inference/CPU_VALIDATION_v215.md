# ThreatStudy v2.1.5 CPU Verification Report

## Executed on the assistant CPU server

- Release integrity: PASS (49 tracked files before final report addition).
- `python -m unittest discover -s tests -q`: **87/87 PASS**.
- 10-source synthetic full matrix replay: **7,680/7,680 simulated records**, analysis PASS; this remains an internal engineering fixture, not actual inference or real nine-publisher evidence.
- Synthetic checkpoint alteration: **CHECKPOINT_TAMPER_REJECTED_PASS**.
- Historical v1.5.1 derived results reconciliation and CTINexus file audit: **REAL_DERIVED_EVIDENCE_AUDIT_PASS** (three models; 148 unique CTINexus texts).
- Existing Monte Carlo source-power script: PASS (synthetic simulations, not new empirical findings).
- Python compilation, Bash syntax, and GPU-denial gate: PASS.
- Final read-only corpus auditor: 9 new tests, including URL host spoofing and absence of report metadata; PASS.
- Source-revision, article-index and URL matching checks are implemented for the actual staged data.

## Not executable on this server

The real 10.7 GB APT archive, selected 72 report texts, provenance JSON and complete historical SMAH prepared inputs were *not uploaded* to this environment. Consequently, exact report-level comparisons on the actual selected archive, near-duplicate flag counts and dataset-bound preflight attestation remain unverified here. The previously provided preflight token counts (Qwen 1285, Llama 919, Mistral 1367) are user-submitted evidence rather than measurements made on this server.

A zero near-duplicate flag does not prove semantic independence; the available SMAH comparison baseline is 284 evaluated windows and not all full historical report texts. The final dataset binding also requires generating a fresh attestation within the staged workspace. **The GPU gate remains closed**.

## Next Ubuntu-Qua CPU task

Copy only the new `crosscti/final_cpu_gate.py` module into `/home/uraz/threat-study/aptcorpus_v214_work/crosscti`, run the command in `FINAL_CPU_GATE_v215.md`, and upload `/mnt/g/ThreatStudy/APT_final_cpu_gate_v215.json`. Do not redownload the archive or re-stage the corpus.
