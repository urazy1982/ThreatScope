# ThreatStudy v2.1.2: tokenizer preflight fix

## Why v2.1.1 is not a valid GPU gate

All three tokenizers returned `max_input_tokens: 2`, which is a measurement error, not evidence of short prompts. Some tokenizer versions return a BatchEncoding with two keys and `len()` counts fields instead of tokens. The actual GPU runner uses a 1×N tensor. v2.1.2 updates CPU preflight to call `apply_chat_template(..., return_tensors="pt")`, verify shape, and count N exactly as the runner does. Counts shorter than 64 tokens are rejected. It retains prompt text, models, dataset selection, model revisions, and the research protocol; original v2.1.1 data/checkpoints are not changed.

## Update an existing staged workspace (no restaging or 10.7-GB redownload)

```bash
cd ~/threat-study/ThreatStudy_APT_Corpus_v2_1_2_Tokenizer_Preflight_Fix
source ~/threat-study/.venv/bin/activate
python scripts/verify_release.py
PYTHONPATH="$PWD" python -m unittest discover -s tests -v

# Only replace the CPU preflight module in the staged workspace.
W="$HOME/threat-study/aptcorpus_v211_work"
cp "$W/crosscti/preflight.py" "$W/crosscti/preflight.py.v211_backup"
cp crosscti/preflight.py "$W/crosscti/preflight.py"
cd "$W"
set -o pipefail
PYTHONPATH="$PWD" python -m crosscti.preflight --root . | tee /mnt/g/ThreatStudy/APT_tokenizer_preflight_v212.json
```

A good run must show `max_input_tokens` clearly greater than 64, `unequal_windows: 0`, and `ok: true` for each model. Any unequal token counts abort the preflight and require review of the prompts; do not change the design mid-run. This fix does not open the GPU gate. Perform independent-corpus overlap and real-model provenance checks separately.
