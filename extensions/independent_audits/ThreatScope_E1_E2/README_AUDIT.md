# Reproduce independent decision-table audit

This directory contains the original text-free export files, an independently authored `independent_check.py`, `INDEPENDENT_RECOMPUTATION.json`, and `INDEPENDENT_AUDIT_REPORT.md`.

Run with Python 3.10+ standard library only:

```
python3 independent_check.py
```

No GPU, model downloads, pandas, or external data are required. The script checks key uniqueness, E2 prompt-level decisions and window/publisher effects, E2 exact sign-flip p-value, E1 validity counts and three direct matched stability contrasts. It does not validate raw model inference, human reference F1, or the hierarchical bootstrap CI.
