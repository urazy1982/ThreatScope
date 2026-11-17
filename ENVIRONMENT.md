# Computational environment

| Item | Value |
|---|---|
| GPU | 1 × NVIDIA GeForce RTX 5090 (32 GB) |
| CUDA | 12.8 |
| PyTorch | 2.10.0+cu128 |
| Transformers | 5.22.2 |
| bitsandbytes | 0.50.2 (NF4, compute dtype bfloat16, double quantisation off) |
| Attention | SDPA |
| Decoding | greedy, `num_beams=1`, `max_new_tokens=96` (Arms A, B); seed 20261113 |
| Models | Qwen/Qwen2.5-3B-Instruct `aa8e7253…`, meta-llama/Llama-3.2-3B-Instruct `0cb88a4f…`, mistralai/Mistral-7B-Instruct-v0.3 `c170c708…` (full hashes in `data/config/study.json`) |
| Dataset | CZLi/apt-reports, revision `c06c0183be808d2e7b2bcbdb351426b75c8cde0f` |

The v2.2.1 runner records these versions at the first cell and refuses to continue
on any mismatch; per-cell `environment.json` files inside `checkpoints/` hold the
recorded values. Re-running inference requires the report text, which is not
distributed: rebuild it from the public collection with
`tools/export_report_sources.py` and the identifiers in
`data/prepared/inputs_redacted.jsonl`.

Reproducing every reported statistic needs only Python ≥ 3.10 (standard library):

```bash
python3 reproduce/reproduce_all.py --out results_rerun
```
