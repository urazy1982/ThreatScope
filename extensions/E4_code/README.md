# ThreatScope E4 — Same-bit-width FP4 control (v0.1)

**Purpose.** Evaluate whether the precision × example-index interaction observed for NF4 also occurs under FP4, keeping nominal four-bit storage width and the bitsandbytes loading implementation fixed. This is an explicitly amended E4 design; it **does not run AWQ or GPTQ**. E4 uses the **same frozen 72-report, eight-publisher E3 interior-window holdout**, so it does not constitute another independent corpus or newly untouched holdout.

**Experimental cells.** Qwen2.5-3B-Instruct and Llama-3.2-3B-Instruct, pinned to the same revisions as E3; FP4 adds 72 windows × 8 example digits × 2 models = **1,152 new generations**. BF16 and NF4 decisions for the exact same windows are reused from the previously completed E3 record table (SHA-256 `e750458e3a91688601255d15a6507adeeeb8c54f48d803064f25af0559ba4d5f`). A full inference rerun is unnecessary.

**Input identity.** E3 input must hash `84c02a30c6f077d1c2d0e645be480616e66d93dd61ca5d660acb77bed37216b3`, and the exact E3 v0.3 selection gate must be present. The 72 texts **are not redistributed** in this kit.

**Primary comparison.** For each publisher, compute the original Arm A index-association statistic D in BF16, NF4 and FP4. Report the publisher-equal contrast `(D_FP4 − D_NF4)` for each model, with publisher-level exact two-sided sign-flip p-values and Holm-2 adjustment across the two primary models. Also report `D_FP4 − D_BF16` and historical `D_NF4 − D_BF16` as secondary descriptions. For invalid model responses, use the frozen Arm A invalid-as-empty rule. Eight publishers provide limited statistical resolution; tests are exploratory and conditional on sign-exchangeability.

**Controls.** Same historical Arm A prompt, parser, greedy sampling (`do_sample=False`, `num_beams=1`), `max_new_tokens=96`, `max_input_tokens=8192`, BF16 compute dtype, model revisions, frozen windows, and software stack as E3. The quantization format changes from NF4 to FP4; in FP4, the runner checks both the model configuration and actual `Linear4bit` quantization states. This tests **format under one implementation**, not a cross-backend comparison; bit width alone does not make distributions or kernels identical.

## Installation on Ubuntu/WSL

Download the ZIP first to `C:\Users\uraz\Downloads`. From Ubuntu:

```bash
mkdir -p ~/threat-study/ThreatScope_E4_FP4_v0_1
unzip -o /mnt/c/Users/uraz/Downloads/ThreatScope_E4_FP4_v0_1_2026-11-15.zip -d ~/threat-study/ThreatScope_E4_FP4_v0_1
cd ~/threat-study/ThreatScope_E4_FP4_v0_1
source ~/threat-study/.venv/bin/activate
python3 tools/verify_package.py
bash run_preflight.sh
```

CPU preflight checks frozen E3 report input and the exact 3,456-row E3 decision-table SHA. It does not load weights or use the GPU.

When the GPU is idle:

```bash
bash run_smoke.sh
```

A passing two-window, 16-checkpoint smoke test creates `H:\ThreatScope\E4\v0_1\smoke_PASS.json`. Then run:

```bash
bash run_full.sh
```

The launcher runs cells serially and resumes only validated checkpoints. It refuses competing GPU compute processes before launching an incomplete cell. The full 1,152-checkpoint audit must pass before analysis output is published.

**Output.** Working checkpoints and full raw model replies stay in `~/threat-study/ThreatScope_E4_FP4_v0_1/results/E4/`. Compact **text-free** result tables, audit summary and logs are copied automatically to `H:\ThreatScope\E4\v0_1`. Historical E1/E2/E3 results and frozen datasets are read-only.

## Validation boundary

The software suite and a text-free, SHA-pinned historical E3 reanalysis run on the assistant CPU environment. The actual 72-window E3 input and approved selection gate are only on your Ubuntu machine, so **the complete live preflight and CUDA smoke are not claimed to have run on this server**. If real FP4 inference cannot load due to model/accelerator compatibility, stop and report the exact error; do not change quantization type, seed, model revision, or dependencies silently.
