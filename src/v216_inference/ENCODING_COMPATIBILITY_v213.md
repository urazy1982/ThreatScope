# v2.1.3 – CPU/tokenizer encoding compatibility

The observed tokenizer returned a mapping without `.shape`. The v2.1.2 preflight rejected it, and the same issue affected `run_cell` GPU inference. This release adds `chat_input_ids` to normalize tensor or BatchEncoding return values without tokenization changes. It validates shape (one row), integer token IDs, and no negative IDs. Both CPU preflight and GPU runner use the same normalization. This does not alter the frozen model, prompts, decoding, dataset, or identities. Run full real-tokenizer preflight and overlap verification before GPU inference.

To install in an existing staged workspace, copy exactly `crosscti/token_encoding.py`, `crosscti/preflight.py`, and `crosscti/runner.py` from this release to the workspace after backing up originals. Do not copy the entire release over the staged workspace.
