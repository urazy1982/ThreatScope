# ThreatStudy v2.1.5 — independent CPU gate

This release makes no scientific claim of zero semantic overlap. It adds a read-only deterministic final audit on the staged v2.1.4 corpus. It does **not** enable GPU execution.

The new audit checks the 72 full staged reports and their source URLs against index-linked file hashes, the nine-publisher balance, the raw selected dataset fingerprint, baseline SMAH window data, exact sentence overlap and high-containment five-word shingles. Results are linked to dataset/input/config SHA-256 hashes.

The previously produced tokenizer report may be supplied for review, but it does not contain a dataset/input hash and therefore cannot fully attest that it belongs to the frozen sample; any subsequent GPU-enabled protocol must record this bound check.

On the Ubuntu-Qua workspace, run:

```bash
cd ~/threat-study/aptcorpus_v214_work
source ~/threat-study/.venv/bin/activate
cp ~/threat-study/ThreatStudy_APT_Corpus_v2_1_5_Final_CPU_Gate/crosscti/final_cpu_gate.py crosscti/
PYTHONPATH="$PWD" python -m crosscti.final_cpu_gate \
 --root . \
 --smah-inputs "$HOME/threat-study/fixation_v151/outputs/prepared/inputs.jsonl" \
 --preflight /mnt/g/ThreatStudy/APT_preflight_v214.json \
 --out /mnt/g/ThreatStudy/APT_final_cpu_gate_v215.json
```

A near-duplicate flag is a stop-for-review, not proof of duplicated reports; a zero-flag result also cannot rule out semantically similar documents. The cross-corpus review is limited to the 284 previously evaluated SMAH windows, not all original full SMAH reports.
