# Run on Ubuntu-Qua

Unpack this release to `~/threat-study/ThreatStudy_APT_Corpus_v2_1_1_NinePublisher`, activate the existing venv, and verify the release. Reuse the original APT index and archive; do not download either again.

```bash
cd ~/threat-study/ThreatStudy_APT_Corpus_v2_1_1_NinePublisher
source ~/threat-study/.venv/bin/activate
python scripts/verify_release.py
PYTHONPATH="$PWD" python -m unittest discover -s tests -v
PYTHONPATH="$PWD" python -m corpusapt.acquire stage \
 --meta "$HOME/threat-study/aptcorpus_metadata" \
 --archive "$HOME/threat-study/external/apt-reports-release.zip" \
 --workspace "$HOME/threat-study/aptcorpus_v211_work" \
 --base-study "$PWD" \
 | tee /mnt/g/ThreatStudy/APT_stage_v211_summary.json
```

The workspace must be new and must not contain GPU outputs. After stage, run preflight and overlap gates in the workspace. `gpu_gate` will remain CLOSED in the staging summary by design.
