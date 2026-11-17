# Next external execution boundary

The CPU server has verified the archived predictions and code, built and tested the v2.2 mechanisms, and generated a fixed replication manifest. **No new v2.2 inference occurred.**

The immediate command on Ubuntu-Qua is CPU-only and does not require the 5090:

```bash
cd ~/threat-study/v22_core_cpu
source ~/threat-study/.venv/bin/activate
PYTHONPATH="$PWD" python -m v22core.tokenizer_gate \
  --archive reference/ThreatStudy_v216_Complete_Results.zip \
  --out /mnt/g/ThreatStudy/v22_core_tokenizer_gate.json
```

If it fails, **do not launch GPU**; share the exact failure. The tokenizer gate is intentionally stricter than old v2.1.6 preflight, especially about end-of-turn tokenization. Real model weights, the new decoding library/implementation, and a verified GPU runner are still required before B/C execution.

The 432-call Arm A replay manifest is in `results/v22_replication_manifest.json`; it is an *execution plan*, not completed GPU evidence. The short-cycle new-workload target is 13,824 B/C model evaluations, plus 432 Arm A consistency calls. These are calls, not a reliable wall-time estimate.

No human gold labels, INT8/GPTQ or 14B work was performed.
