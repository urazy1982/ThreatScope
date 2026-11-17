# ThreatScope E3 GPU v0.4

Retrospective **same-source-archive unseen-report** validation. The 72 E3 windows were selected under E3 v0.3 gate, which is treated as read-only and checked against immutable SHA-256 `84c02a30c6f077d1c2d0e645be480616e66d93dd61ca5d660acb77bed37216b3`.

This kit does NOT re-select reports. It uses precisely the historical Arm A system instruction, prompt construction, parsing, model revisions, BF16/NF4 format and greedy generation setting from the ThreatScope v1.0.0 archive (historical core copied as `vendor/core.py`). The input source and publisher distribution are different, so this kit has a separate experiment protocol. Results are exploratory/posthoc and not prospective preregistered.

**Installation:** download ZIP to `C:\Users\uraz\Downloads`, extract in `~/threat-study/ThreatScope_E3_GPU_v0_4`.

Run `bash run_preflight.sh`, then `bash run_smoke.sh`, then `bash run_full.sh`. GPU work is sequential, one model at a time. A busy-GPU check runs before a new incomplete cell and will block rather than preempt competing jobs. Full output checkpoints remain on Ubuntu; text-free CSV, audits and logs are copied to Windows `H:\ThreatScope\E3\v0_4`.

`results/reports/E3_decisions_textfree.csv` and `E3_window_effects.csv` do not include report text. Result rows are anonymized to report/window IDs, although IDs and hashes alone are not anonymity guarantees. Share only after disclosure review.

Required inputs: `~/threat-study/ThreatScope_E3_v0_3/inputs_E3_private.jsonl`, `/mnt/h/ThreatScope/E3/v0_3/GATE.json`. The all-cell analysis requires 3456 valid **checkpoints**, not necessarily 3456 schema-valid model outputs; invalid JSON is retained as a meaningful outcome. Confidence intervals are not calculated in this starter; eight-publisher sign-flip p-values are exploratory and do not resolve multiple-testing or generalization concerns.
