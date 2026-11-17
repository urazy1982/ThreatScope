# CPU validation report

On the assistant server, with user-supplied frozen full-text inputs reconstructed privately from the uploaded historical archive:

- Dataset identity SHA-256 exactly `e22310e37efe29c2f29f8ec51b931d765a371cc9f7628b52337fa86ce338500b`.
- E2 text and configuration preflight: 3 models × 2 precisions = **6/6 PASS** on all 144 real windows.
- Archived Arm C original record SHA-256: **6,912/6,912 PASS**.
- Archived prompt hash against authentic frozen source and historical SYS_SINGLE: **6,912/6,912 PASS**.
- Recomputed archived window-level D from original winners: **432/432 PASS**, maximum numerical difference 5.6e-17.
- Full **2,304 synthetic E2 records** (Qwen BF16 + NF4, matching historical winners by construction) successfully exercised the analysis pipeline: ZERO contrast, 100% agreement as expected by construction. **This is mock software testing and not a real experiment.** Mock checkpoints were deleted.
- Deliberately altered synthetic checkpoint: **REJECTED PASS**.
- Python/compile/regression tests: see actual test run output and SHA-256 manifest.

E2 GPU inference has **not** been executed by the assistant server, which lacks the user's CUDA GPU and pinned model weights. E1 raw checkpoint analysis must run on Ubuntu as `bash run_e1_diagnostic.sh`; only its submitted aggregate summary was available here.
