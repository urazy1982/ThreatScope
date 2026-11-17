# v2.2.1 local amendment — 2026-11-13

Scientific design is inherited from `V22_CORE_PROTOCOL_AMENDMENT.md`, with the following frozen implementation clarifications. This record does not claim external preregistration.

1. Arm C candidate continuation consists of canonical JSON `{"relevant":[j]}` followed by the model-specific end-of-turn token, with *no template trailing newline in the scored continuation*. In real Qwen chat-template rendering, a final newline outside that continuation is acceptable. Only that single exact suffix is permitted by the tokenizer check.
2. Arm C is evaluated with eight **serial forward passes per prompt** by default to fit a 32-GB GPU. It sums token log-probabilities (not length-normalized), verifies finite scores, retains softmax mass and all eight scores, and resolves exact ties to the lowest index.
3. Arm B grammar permits exactly the 256 canonical ascending JSON subsets. Generation uses a token-prefix allowed-token callback and terminates with the authenticated end-of-turn marker; noncanonical outputs are protocol violations.
4. The 432-call v2.1.6 replay is a distinct consistency check. Raw bytes, selected indices, and output validity must be reported separately. No arbitrary output agreement threshold is used to retrospectively discard v2.1.6 results. Inference-arm metadata captures environment and source hashes, and an analysis of drift must be in the manuscript.
5. Execution order is frozen: replay, then Arm C, then Arm B. New data may not be mixed with older checkpoints. Existing records are validated before resumption. Existing v2.1.6 inputs and checkpoints remain unchanged.
6. Exact two-sided publisher sign-flip tests use nine publishers, with Holm within each arm over three models and secondary Holm across six tests. These are additional tests after v2.1.6 was observed; caveats about protocol registration must be reported.
7. Package runtime version sets a software lock from the first GPU cell; subsequent cells must match. No CPU offload is allowed.

This amendment's SHA-256 and source hashes are bundled in `RELEASE_HASHES.json` and signed into the local dataset-bound authorization generated on the researcher's environment.
