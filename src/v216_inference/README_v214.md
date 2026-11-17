# ThreatStudy APT v2.1.4 — exact sentence overlap repair

This is a pre-inference data-quality amendment to v2.1.1. It does not alter model prompts, model revisions, anchor indices, or scoring. It preserves nine publisher groups, eight reports per group, 144 windows and 6,912 planned model calls.

Observed pilot overlap: eight exact normalized sentences across two report IDs (`f81d433e09045f0940cec245`, `84863dfded11cc2e33a05895`) within 284 prepared SMAH windows. The stage command now requires `--smah-inputs` and excludes any proposed APT report containing **any** matching sentence from its full extracted text (not just its two sampled windows). The next eligible report in the original deterministic source-specific URL-hash ordering replaces it. Thus more than two reports can be excluded if matches occur outside sampled APT windows.

**Use a NEW workspace** `~/threat-study/aptcorpus_v214_work`, never overwrite v2.1.1. The old preflight is invalid for new selection. No GPU authorization occurs here.

```bash
cd ~/threat-study/ThreatStudy_APT_Corpus_v2_1_4_Overlap_Repair
source ~/threat-study/.venv/bin/activate
python scripts/verify_release.py
set -o pipefail
PYTHONPATH="$PWD" python -m corpusapt.acquire stage \
  --meta "$HOME/threat-study/aptcorpus_metadata" \
  --archive "$HOME/threat-study/external/apt-reports-release.zip" \
  --workspace "$HOME/threat-study/aptcorpus_v214_work" \
  --base-study "$PWD" \
  --smah-inputs "$HOME/threat-study/fixation_v151/outputs/prepared/inputs.jsonl" \
  | tee /mnt/g/ThreatStudy/APT_stage_v214_summary.json
cd ~/threat-study/aptcorpus_v214_work
PYTHONPATH="$PWD" python -m crosscti.preflight --root . \
  | tee /mnt/g/ThreatStudy/APT_preflight_v214.json
```

The old 284 SMAH windows are **not** a substitute for a full-document SMAH overlap review; detect near duplicates (e.g. syndicated stories or paraphrases) separately. No GPU inference is authorized solely by this amendment.
