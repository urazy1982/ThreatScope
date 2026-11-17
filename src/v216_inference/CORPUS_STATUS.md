# Independent corpus progress and scientific constraints

- CTINexus audit input has 298 files, 148 unique report texts, zero source tags. This rules it out for publisher-cluster inference.
- CTI-Crawler source catalog formally lists publisher-focused sources, with verifiable publisher website/domain references. The separate [APT release](https://huggingface.co/datasets/CZLi/apt-reports) lists `filename_map.json`, `classifications.json`, `source_risks.json`, and a large `apt_github_distribution_20260922T211548298793Z.zip` archive. Its documentation reports 3,051 records total, including 1,023 in APT publisher sections. The archive is about 10.7 GB.
- The prior study's 5-source exact test p=0.0625 warns against report pseudoreplication. Ten identified sources permit p resolution down to 0.001953125 (two-sided), but the test's interpretability still depends on actual source-level independence and comparable articles.
- Source ID means collector-attributed publishing organization, not automatically an independently certified editorial source of every word. Original URL host, index linkage and ZIP path are separately checked. Further manual/CPU sample review remains required.
- Selection uses **no model outcomes**. The initial pool excludes flagged or non-English categories and is frozen before selection.
- The primary balanced-index contrast is sensitive to set-size and positional interactions. Accuracy is not estimated without independent sentence labels. Maintain cardinality, JSON-validity and direct switching diagnostics.
- The staging package is intentionally **not GPU-ready**. Do not bypass the gate by editing `source_provenance_status` or copying a prior GPU script into this workspace.
