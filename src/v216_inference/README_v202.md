# ThreatStudy Cross-Corpus v2.0.2 — CPU-only audited hardening

This is a **separate immutable experimental-development release** derived from v2.0. The unmodified original v2.0 input, code and scientific results remain intact. No real independent-corpus model predictions are contained or implied.

### What is included

- `crosscti/`: original eight-anchor analysis plus improved cross-source duplicate rejection and fail-closed GPU runner.
- `tests/`: 37 deterministic CPU tests.
- `scripts/cpu_replay.py`: full 7,680-record *synthetic* checkpoint replay.
- `scripts/evidence_audit.py`: independent calculations on the previously uploaded authentic v1.5.1 CSVs and CTINexus duplicate audit.
- `scripts/source_power_simulation.py`: publisher-level Monte Carlo reference under explicitly synthetic assumptions.
- `evidence/`: original uploaded derived evidence (not GPU raw checkpoints) and audit JSON outputs.
- `CPU_VALIDATION_REPORT.md`: detailed completed tests, interpretation, limitations, and next gates.
- `RELEASE_HASHES.json`: sha256 of all substantive release files.

### Run on a CPU-only machine

```bash
cd /path/to/ThreatStudy_v2_0_2_CPU_Hardened
python3 scripts/verify_release.py
PYTHONPATH="$PWD" python3 -m unittest discover -s tests -v
PYTHONPATH="$PWD" python3 scripts/cpu_replay.py --root .
PYTHONPATH="$PWD" python3 scripts/evidence_audit.py \
 --ctinexus-audit evidence/CTINexus_provenance_audit.json \
 --v151-zip evidence/ThreatStudy_v151_Analysis_Results.zip \
 --output evidence/real_evidence_results.json
python3 scripts/source_power_simulation.py --output evidence/source_power_simulation.json
```

`numpy` is required only for the Monte Carlo simulation. Other CPU tests use the Python standard library.

### GPU intentionally blocked

The corpus lacks authenticated publisher-level metadata in the present evidence. `scripts/run_gpu.sh` will report `GPU_PROVENANCE_GATE_CLOSED`. That is a scientific safeguard, not an installation failure. We will release a new GPU-ready protocol only after source/article provenance, duplication and tokenizer gates pass with **real** eligible report files.
