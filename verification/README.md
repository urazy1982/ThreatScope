# Independent recomputation of extensions E1–E4

`recompute_extensions.py` recomputes every E1–E4 quantity reported in the manuscript
*One Digit, Different Decisions: Quantization-Dependent Prompt Sensitivity in Cyber-Threat Intelligence*
(Section 6 and Supplementary Section S10). It was written for the manuscript audit, separately from the
analysis scripts in `extensions/`, and uses the Python standard library only.

```bash
python3 verification/recompute_extensions.py          # writes verification/recomputed_extensions.json
```

What it does:

- **E1, E2:** reads the text-free decision tables in `extensions/E5_synthesis/evidence/`.
- **E3, E4:** parses the 4,608 raw model outputs in `extensions/E3_checkpoints/` and `extensions/E4_checkpoints/`
  itself under the Arm A output rule, and reports any disagreement with the recorded validity and indices
  (`parser_mismatches`; 0 for this release).
- Estimand: example-index dependence D (manuscript Eq. 1), aggregated window → report → publisher with equal
  weights (E1 primary rule: window → publisher, as fixed in its protocol).
- Tests: exact two-sided publisher sign-flip test (publisher values within 1e-9 of zero count as ties), Holm
  adjustment within each extension. Bootstrap intervals (10,000 resamples, seed 20261116) are descriptive.

`recomputed_extensions.json` is the output for this release; it is identical to the values used in the manuscript.
