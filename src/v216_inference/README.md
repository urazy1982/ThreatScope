# ThreatStudy — APT Publisher Corpus v2.1.0 (CPU acquisition release)

**Status:** CPU software validated; real publisher-labeled data acquisition pending; **GPU deliberately closed**.

This is a new, source-audited corpus workflow superseding the CTINexus source selection in v2.0.2. The original v2.0.2 software is included as a tested reference. Do not treat the old `config/study.json` as the selected APT data configuration: the staging command writes an independent, newly versioned workspace only after the true dataset is checked.

## Why CTINexus is not our confirmatory corpus

The real repository audit found 298 JSONs but only 148 unique report texts, all under annotation, and zero publisher tags. It cannot support the 10-publisher inferential protocol. No sources were invented.

## Real dataset selected for validation

Original publisher-tagged release: [CZLi/apt-reports](https://huggingface.co/datasets/CZLi/apt-reports), collected with [CTI-Crawler](https://github.com/peng-gao-lab/cti-crawler). It publishes a ~10.7 GB archive and separately accessible source/URL indexes. Use **only the `02_APT_publishers` articles** for our first confirmatory sample, excluding MITRE references and broader activity reports. The release describes 1,023 publisher-APT articles; this count has **not been independently replicated on our CPU server**. The upstream README warns that a publisher's APT section may still contain some non-APT material. Original publishers retain copyright; the release is for noncommercial academic/security research. Preserve attribution; do **not** include full articles in uploaded evidence or public code packages.

Publisher candidates, in predeclared order: `securelist_apt`, `eset_apt_reports`, `thehackernews_apt`, `trendmicro_apt`, `unit42_apt`, `bitdefender_apt`, `talos_apt`, `groupib_apt`, `volexity_apt`, `sentinellabs_apt`, `asec_apt`, and `sophos_pacific_rim`. Explicitly exclude Microsoft, Sekoia and CERT-UA from this initial English publisher-stratified design because of documented content-mix/language concerns. This restriction is a methodological choice, not a claim that the excluded publications lack quality.

## Phase 1: Metadata-only CPU gate (a few MB)

In `Ubuntu-Qua`, with existing ThreatStudy venv enabled:

```bash
cd ~/threat-study/aptcorpus_v21
source ~/threat-study/.venv/bin/activate
python scripts/verify_release.py
PYTHONPATH="$PWD" python -m unittest discover -s tests -q
PYTHONPATH="$PWD" python -m corpusapt.acquire metadata --dest "$HOME/threat-study/aptcorpus_metadata"
PYTHONPATH="$PWD" python -m corpusapt.acquire inspect --meta "$HOME/threat-study/aptcorpus_metadata" \
    | tee /mnt/g/ThreatStudy/APT_index_inventory.txt
cp "$HOME/threat-study/aptcorpus_metadata/source_inventory.json" /mnt/g/ThreatStudy/APT_source_inventory.json
```

The inventory includes a `gate_pass` flag. **If false, stop:** metadata format/coverage is not authenticated. Send `APT_source_inventory.json` for adapter revision. Do not hand-enter publisher tags or edit model data.

## Phase 2: Only if real metadata gate passes

A large download (~10.7 GB), not to be run until the first stage succeeds. It is explicitly opt-in and resumable using Hugging Face Hub; ensure enough local WSL disk space. Keep raw corpus on the Ubuntu disk, not automatically mirrored to G:.

```bash
cd ~/threat-study/aptcorpus_v21
source ~/threat-study/.venv/bin/activate
PYTHONPATH="$PWD" python -m corpusapt.acquire download \
  --meta "$HOME/threat-study/aptcorpus_metadata" \
  --dest "$HOME/threat-study/external/apt-reports-release.zip" --confirm-large
PYTHONPATH="$PWD" python -m corpusapt.acquire stage \
  --meta "$HOME/threat-study/aptcorpus_metadata" \
  --archive "$HOME/threat-study/external/apt-reports-release.zip" \
  --workspace "$HOME/threat-study/aptcorpus_v21_work" \
  --base-study "$PWD" | tee /mnt/g/ThreatStudy/APT_stage_summary.json
```

The script examines linked HTML entries *inside* the ZIP without extracting the entire 10.7 GB archive. It requires at least 10 eligible independent publisher identifiers, selects eight reports from each with a frozen SHA-256 salt, rejects repeated URLs, duplicated text and strong near-duplicates, verifies archive CRC when reading, and creates **160 windows**. If successful, the planned 3-model × 2-precision × 8-example budget is **7,680 GPU calls**; the experiment itself is **not** launched.

## Phase 3: Real-tokenizer and corpus-overlap CPU gates

```bash
cd "$HOME/threat-study/aptcorpus_v21_work"
source ~/threat-study/.venv/bin/activate
PYTHONPATH="$PWD" python -m crosscti.preflight --root . | tee /mnt/g/ThreatStudy/APT_tokenizer_preflight.json
```

The eight examples must tokenize to equal lengths for each window in every model. Also inspect `dataset/corpus_provenance.json` (contains original article URLs/hashes, but no source report text) and compare against the SMAH-CTI original for overlap. A CPU quality review of several selected articles is required before treating the source labels as professionally authenticated.

**Do not run the GPU from this release.** The runner and shell launcher fail closed. The GPU-ready release will be made only once we have the real index, content and tokenizer reports.

## What is and is not validated on my CPU server

- **Validated:** code syntax, 37 original v2.0.2 regression tests, acquisition/index spoofing and hash tests, simulated source-archive linkage, full 80-report/160-window preparation using a *synthetic archive*, the 7,680-record *synthetic inference replay*, and fail-closed GPU behavior.
- **Not independently validated:** actual HF archive contents, real index JSON schema, 80 real article extraction results, article-level semantic quality, publisher domain accessibility, SMAH overlap and real model tokenizer preflight. The execution environment has no direct external file-download access.

No real GPU predictions are present in this release. The original v1.5.1 dataset, checkpoints and results are unchanged.
