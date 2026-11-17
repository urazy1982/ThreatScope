Run `bash scripts/run_all_cpu.sh` to reproduce all executable CPU experiments. Existing outputs in `results/` will be regenerated deterministically. The separate local tokenizer check is `bash scripts/run_tokenizer_cpu_ubuntu.sh` and requires the pinned Hugging Face tokenizers on Ubuntu-Qua; it is not part of the server's CPU PASS total.

The original v2.1.6 94-test suite is available separately as `bash scripts/run_upstream_cpu.sh` to isolate its potentially longer CPU test runtime. It was successfully run independently before packaging.
