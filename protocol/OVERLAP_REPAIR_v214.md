# ThreatStudy v2.1.4 — Data independence amendment

This revision is made **before any v2 GPU inference**. In the v2.1.1 sample, two APT reports contained eight sentence strings that also occurred in the earlier SMAH prepared windows. v2.1.4 reruns report selection from the immutable original APT archive and original publisher metadata. It retains the nine-source order and frozen SALT and skips candidate reports whose **entire extracted text** contains any normalized sentence already present in the 284 original SMAH windows, replacing them with the next report in deterministic URL-hash order from the same publisher.

Selection is label-blind and model-outcome-blind. It does not edit individual windows or overwrite old staged inputs. A new dataset digest and protocol ID are recorded; previous v2.1.1 tokenizer preflight cannot certify the replacement sample. The exclusion list and hashed shared sentences are recorded in `dataset/corpus_provenance.json` and can be audited without distributing the protected original report text.

Limitation: full-report *semantic* near-duplicates and SMAH sentences outside its 284 evaluated windows remain unverified. This exact-sentence pass is necessary, not sufficient, for broad cross-corpus independence. Do not open GPU gate solely on its success.

## Ubuntu-Qua

After copying this release to `G:\ThreatStudy` and unzipping beside the earlier releases:

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
```

Rerun real tokenizer preflight in the **new** workspace and retain the source/archive/protocol manifest.
