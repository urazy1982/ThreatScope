# v2.0.2 CPU hardening — controlled changes

- Modified `crosscti/prepare.py`: reject identical/whitespace-normalized article text even when assigned different source labels; protects source-level independence.
- Modified `crosscti/runner.py` and `scripts/run_gpu.sh`: fail-closed GPU provenance gate because no real authenticated publisher-level dataset was available.
- Changed `config/study.json` protocol string to a new version and clearly marked source authentication unverified; incompatible with prior GPU result manifests by design.
- Added 25 CPU tests: deduplication, exact inference, index symmetry, statistical nonidentifiability by cardinality, integrity/tamper, fake tokenizer parity, and GPU gate.
- Added reproducible audits of **real uploaded derived** results and hypothetical source-level power; labels distinguish these from the synthetic 7,680-record replay.
- Preserved all other statistical definitions; no inference data and no prior checkpoint files were altered.
