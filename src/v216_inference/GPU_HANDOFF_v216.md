# ThreatStudy v2.1.6 — frozen GPU handoff

This **does not** pretend the source archive is present on the CPU server. The first Ubuntu-Qua step reruns the real selected-corpus provenance/overlap audit and the three real tokenizer tests, then binds all evidence to exact hashes. Model weights are not loaded until after authorization.

- Required workspace: `~/threat-study/aptcorpus_v214_work` (72 reports; 144 windows)
- Required historical baseline: `~/threat-study/fixation_v151/outputs/prepared/inputs.jsonl`
- Frozen real report SHA-256: `461682f329a5cca95715d6d7a12356dddb3f38f3adf0e221a2443bdecfdd354e`
- Planned calls: 6,912 (9 sources × 8 reports × 2 windows × 8 anchors × 3 models × 2 precisions)
- Limitations: historic SMAH comparison only uses selected windows; five-word shingle screen is not semantic identity proof. Collection is a distinct source corpus, not guaranteed novel underlying event narratives.

## Commands (sequential, no tmux)

From the v2.1.6 release directory after `source ~/threat-study/.venv/bin/activate`:

```bash
bash scripts/prepare_gpu_handoff.sh "$HOME/threat-study/aptcorpus_v214_work" "$HOME/threat-study/fixation_v151/outputs/prepared/inputs.jsonl"
```

Inspect `~/threat-study/aptcorpus_v214_work/outputs/authorization/gpu_authorization.json`. If authorization fails, **do not** run inference. If it passes:

```bash
bash scripts/run_gpu.sh "$HOME/threat-study/aptcorpus_v214_work" 2>&1 | tee "$HOME/threat-study/aptcorpus_v214_work/gpu_run.log"
```

Separate terminal:

```bash
cd ~/threat-study/aptcorpus_v214_work
bash scripts/status.sh
```

This launcher runs the real data on RTX 5090 **only after CPU authorization** and verifies the authorization before each model-precision cell. Checkpoints are resumed, not regenerated. Changing configuration, data, prompt module, tokenizer/preflight, model revision or runner invalidates authorization. Full-dataset/source hashes and stored provenance attestations are checked; original 10.7 GB archive is not rehashed on every cell. No GPU results or findings are included.
