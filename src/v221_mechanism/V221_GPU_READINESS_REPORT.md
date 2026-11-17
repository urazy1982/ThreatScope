# ThreatStudy v2.2.1 — GPU-readiness and corrected real-tokenizer gate

**Manuscript title:** One Digit, Different Decisions: Quantization-Dependent Example Sensitivity in Structured Cyber-Threat Intelligence Relevance Selection.

**Status:** LOCAL SOFTWARE/CPU VALIDATION. All **real v2.2.1 GPU calls remain NOT EXECUTED**. This package is NOT externally preregistered. The real-tokenizer gate result below was **reported by the researcher** from Ubuntu-Qua and has NOT been independently rerun on this server. A fresh rerun from this specific versioned release is mandatory before a GPU run is authorized.

## Why v2.2.1 was necessary

The previous gate incorrectly required `apply_chat_template(messages + assistant_turn)` to be *exactly* `apply_chat_template(messages, add_generation_prompt=True)` + JSON candidate tokens + end-of-turn token. The real Qwen tokenizer adds exactly one trailing newline token **after** the end-of-turn marker. The actual observed Qwen diagnostic was 179/179 matching tokens, with full-chat length 180 and one extra token ID 198 (newline). This is outside the candidate's likelihood-scoring span.

The corrected gate accepts **only** an exact match or an exact match followed by precisely one tokenizer-encoded newline. It does not modify the prompt, the scored candidate, or the model's end-of-turn token, and does not accept any other suffix.

## Real tokenizer output reported by researcher

| Tokenizer revision | Arm B max | Arm C max | B/C imbalance | Candidate token lengths | Template mismatch | Trie subsets |
|---|---:|---:|---|---|---:|---:|
| Qwen2.5-3B `aa8e7253…` | 1,285 | 1,314 | 0 / 0 | 6 × 8 | 0 | 256 |
| Llama-3.2-3B `0cb88a4f…` | 919 | 948 | 0 / 0 | 6 × 8 | 0 | 256 |
| Mistral-7B `c170c708…` | 1,367 | 1,398 | 0 / 0 | 8 × 8 | 0 | 256 |

Reported dataset SHA-256 `461682f329a5cca95715d6d7a12356dddb3f38f3adf0e221a2443bdecfdd354e`; prepared-input SHA-256 `e22310e37efe29c2f29f8ec51b931d765a371cc9f7628b52337fa86ce338500b`. The package reruns this check locally and binds the local JSON file's SHA-256 to the GPU authorization.

## CPU validation and scientific controls

- Existing v2.2-Core CPU tests are carried forward and extended with real-template boundary regression, no-extra-suffix assertions, teacher-forced serial scoring, model revision and dataset gate rejection, and checkpoint tamper rejection.
- Arm C computes **8 conditional log-probability sums per prompt**, including each model's verified end-of-turn token. It uses a *serial* 8-candidate implementation to reduce peak GPU memory and retains all 8 scores and normalized candidate mass.
- Arm B restricts output to **256 canonical ascending-index JSON subsets**. This is not equivalent to allowing all parser-valid JSON strings. The canonical restriction is a decoding intervention and must be disclosed.
- Arm A environment replay compares raw byte identity, parsed selected indices, and validity separately. A mismatch is reported, not silently ignored and not an automatic reason to discard the original v2.1.6 archive. A source/report-level analysis is performed for Arms B and C only when all new calls are present.
- The original 6,912 v2.1.6 records are retained without modification. The new planned workload is **432 replay + 6,912 Arm C + 6,912 Arm B = 14,256 calls**.
- No human gold labels, no gold-defined false positives, and no additional INT8/GPTQ/14B arms are included.

## Real GPU runtime limitations

The actual Hugging Face model weights and CUDA/quantization kernels are unavailable on this CPU server. Accordingly, the v2.2.1 GPU runner, generation-prefix callback, and serial scorer have CPU unit/integration coverage but **have not been tested with the actual three weight checkpoints**. Model compatibility and inference speed must be checked on the user's RTX 5090.

Before any model load, the local runner checks the frozen release hashes, source and input fingerprints, model revisions, real local tokenizer gate, and authorization hash. Checkpoints use atomic writes and per-record hashes. A cross-cell environment lock prevents mixing model outputs from different software/CUDA versions after the first run. Greedy replay is still not guaranteed bitwise deterministic; all differences are retained.

## Preregistration and rights

The earlier v2.2 protocol was drafted after v2.1.6 outcomes were observed. This software fixes the analysis path and produces a local provenance record, **not a timestamped OSF registration**. If the author wants to call B/C tests preregistered, they should register this amendment and the source hash publicly before seeing new outputs. Otherwise describe the tests as planned prospective extensions, not independently preregistered hypotheses.

The reference archive contains selected publisher-sourced text. Do not redistribute this private executable package publicly without checking source-text licenses. Public supplement should instead use hashes, report IDs/URLs, retrieval instructions and redistributable code.

## Additional CPU mock-run integration verification

The private CPU validation additionally exercised a **synthetic authorization** against the full 6,912-record archived baseline, verified authorization tampering was rejected, wrote 72 replay checkpoints through the real resumable filesystem implementation using stubbed model outputs (no real inference), and confirmed a deliberately corrupted checkpoint fails a subsequent audit. This synthetic integration test is not evidence of RTX 5090 inference or actual replay agreement.
