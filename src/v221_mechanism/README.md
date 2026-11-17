# One Digit, Different Decisions

**Quantization-Dependent Example Sensitivity in Structured Cyber-Threat Intelligence Relevance Selection**

## ThreatStudy v2.2-Core — CPU evidence and software-validation package

Status: **CPU COMPLETE; GPU ARMS B AND C NOT YET EXECUTED; v2.2 protocol NOT REGISTERED.**

This package is an independently executable research-validation artifact, not a new GPU result. It includes the actual 6,912-record v2.1.6 archive provided by the researcher, a fresh analysis of those records, a 13,824-record **explicitly synthetic** v2.2 Arm B/C replay, 256-output constrained JSON validator and token-trie implementation, CPU teacher-forced candidate scoring, pinned 432-call environment-replay selection, provenance checks, 10,000-draw cardinality-only null references per model, and tests.

### Quick commands

```bash
python3 scripts/verify_release.py
python3 -m unittest discover -s tests -q
PYTHONPATH=. python3 -m v22core.replay --archive reference/ThreatStudy_v216_Complete_Results.zip --out results
PYTHONPATH=. python3 -m v22core.synthetic --archive reference/ThreatStudy_v216_Complete_Results.zip --out results
PYTHONPATH=. python3 -m v22core.null --archive reference/ThreatStudy_v216_Complete_Results.zip --out results/cardinality_only_reference.json --draws 10000
PYTHONPATH=. python3 -m v22core.replication --archive reference/ThreatStudy_v216_Complete_Results.zip --out results/v22_replication_manifest.json
```

Requirements for basic reanalysis: Python 3.10+, NumPy, PyTorch (CPU). No CUDA or network required. Run `bash scripts/run_all_cpu.sh` for the v2.2 CPU suite, checkpoint replay, and simulations. The original v2.1.6 94-test suite is independently repeatable with `bash scripts/run_upstream_cpu.sh`; it is separate to isolate its runtime.

### Most important new observation

For each 8-prompt window, the original influence score is exactly:

`D = (number_of_own_example_index_hits - total_selected_indices / 8) / 7`.

Consequently, a positive NF4-minus-BF16 interaction need not mean a higher count of own-example hits. In the archived data, Llama has **14 fewer** own-example hits under NF4, but **513 fewer** selected indices overall, resulting in a positive raw interaction. See `CPU_SCIENTIFIC_REPORT.md` and `results/cpu_main_results.json`.

### Contents

- `reference/` — original archived 6,912 checkpoints and frozen v2.1.6 source release
- `protocol/` — original proposed v2.2 DOCX plus reviewed v2.2-Core protocol amendment
- `v22core/` — independent audit, matched estimators, grammar, scoring, synthetic integration, publisher statistics and tokenizer gate
- `tests/` — CPU regression, tamper, statistical, scoring, tokenization and end-to-end tests
- `results/` — empirical reanalysis, **clearly marked simulated data**, null references, replication manifest, provenance/token checks
- `evidence/` — original final CPU gate, tokenizer preflight and independent scientific audit
- `scripts/` — release and CPU verification

### Scientific limitations

1. The new normalized-index-mass metric is **posthoc exploratory**. It is calculated by spreading mass uniformly over each already selected set; it is **not** a model probability or an actual forced-single-choice result.
2. The synthetic 13,824-row Arm B/C matrix does **not** represent real BF16/NF4 predictions.
3. Real tokenizer preflight for the new Arm C instruction, canonical JSON token trie, and exact chat-template continuation boundaries must run on Ubuntu-Qua because this server cannot download the pinned tokenizers.
4. The proposed second human annotator, human gold labels, INT8/GPTQ and larger model are **not included** in this short-cycle Core extension.
5. The v2.2 protocol is a **draft** and was designed after inspecting v2.1.6 results. It has not been registered on OSF. It must be frozen and registered before new B/C inference if confirmatory language will be used.
6. The source release has a limited license status for publisher report texts; do **not publicly redistribute the included reference ZIP** without checking reuse rights. Source hashes and scripts can be shared separately.
