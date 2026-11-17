# ThreatStudy APT Publisher Corpus v2.1.0 — CPU Validation

**Status:** source-code release is tested; actual HF index and article archive remain *not downloaded on this server*. No model inference was performed.

## Dataset decision

- CTINexus: 298 JSON files, 148 exact unique report texts, 0/298 source labels. Its `demo`/`test` copies overlap `annotation`; not a valid independently publisher-stratified confirmation without separate source records.
- CTI-Crawler source code: repository publishes 15 curated `vendor_apt` source entries; the new design prespecifies 12 eligible English publisher IDs and excludes Microsoft, Sekoia and CERT-UA because of content/language concerns, not model outcomes. Source IDs are linked to publisher base URLs from the repository's `vendor_apt.yaml` (blob SHA `f991942a69ba75708c22c981b1f3d006377b6074`).
- Hugging Face corpus: `CZLi/apt-reports` describes 3,051 reports total with 1,023 publisher-APT records in `02_APT_publishers` and provides independently downloadable `filename_map.json`, `classifications.json`, and `source_risks.json`. The full release ZIP is about 10.7 GB and is subject to noncommercial research licensing and original publisher copyrights. These source-reported counts are **not locally verified real-data counts**.

## Tests performed on CPU server

| Gate | Result |
| --- | --- |
| 37 previous pipeline tests | PASS |
| 19 new metadata/archive acquisition tests | PASS |
| Complete unit suite | **56/56 PASS** |
| Full synthetic 10-publisher, 80-report, 160-window preparation | PASS |
| 7,680 synthetic checkpoint / statistical replay | PASS |
| Metadata tampering | Rejected |
| Missing publisher source and mismatched domain | Rejected |
| Path traversal in ZIP | Rejected |
| Insufficient publisher count | Rejected |
| Missing article URL–archive index link | Excluded; counted |
| Cross-publisher duplicate sample | Rejected |
| Metadata download revision pin (mocked public API) | PASS |
| 10.7 GB download consent requirement | PASS |
| CPU-only runner/GPU gate | Closed |
| v1.5.1 real derived evidence replay | PASS (3 models) |

All synthetic experiments use *artificial records* and prove only software behavior. They do not establish a new quantization effect.

## Real-data gates still necessary

1. Download the *small* HF index files on the user's Ubuntu-Qua host (server has no public HTTP/DNS) and check their real schema and 10-source publisher coverage.
2. Once the index passes, download the original 10.7 GB archive and compare source id + original URL + article number + ZIP folder and file hash. The script reads publisher HTML entries in place, not all PDFs.
3. Check a deterministic 80-report/160-window sample, text extraction, duplicates, article-source domain correspondence, real tokenizer equal-length preflight, and SMAH overlap. Manually spot-check collector-reported publishers.
4. Only after all these pass, produce a separately frozen GPU-enabled release. v2.1.0 itself cannot run GPU inference.

## Important interpretive safeguards

- The paper should claim **cross-corpus structured-prompt sensitivity**, not cross-corpus ground-truth CTI extraction accuracy, because the APT collection is not sentence-relevance labeled.
- A balanced example-index contrast can reflect position selection or selection-set size, not necessarily literal copying; use cardinality-matched and direct-singleton diagnostics for interpretation.
- The ten-source exact sign-flip enumeration assumes sign-exchangeability at the source level; it is not a randomized precision assignment experiment. Report source-level uncertainty, sensitivity to publisher count and multiplicity adjustments.
- Original publisher texts remain local. Evidence shared with an independent reviewer should include URLs, hashes and de-identified aggregate diagnostics, not the full copyrighted articles.
