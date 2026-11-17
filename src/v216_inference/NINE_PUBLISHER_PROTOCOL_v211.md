# ThreatStudy v2.1.1 — nine-publisher corpus protocol

The v2.1.0 REAL_CONTENT_SOURCE_COVERAGE_FAIL on the authentic APT release (2026-11-13) found nine qualifying sources (at least eight parseable reports with 16 sentences and 200 words), not ten. The dataset had 10 publishers with >=8 index records, but The Hacker News and ESET had zero qualifying HTML, and Sophos had only three.

This is a **separately versioned pre-inference redesign**, not a silent rewrite of v2.1.0. The primary statistical unit is the publisher, n=9. The frozen corpus selects 8 reports per publisher, 2 windows per report, 8 prompt index interventions per window, 3 models and 2 precisions: 72 reports, 144 windows, **6,912 GPU predictions**. Exact source-level two-sided sign-flip test enumerates 2^9=512 assignments; bootstrap and Holm correction remain applicable. Larger source counts are preferred but the 9-source experiment has adequate exact-test resolution (smallest possible two-sided p=0.00390625).

The source selection order and minimum content requirements are otherwise unchanged. Do not compare a p-value from this sample directly with the old 10-source hypothetical protocol as if both were identical preregistered experiments. Disclose this feasibility-driven amendment in the eventual paper.

The 10-source metadata inventory still represents the preliminary index gate and is not redefined. The 9-source real-content gate is the operative freeze condition.

Old folder and original 10.7 GB archive are NOT modified. GPU inference remains deliberately closed until actual corpus overlap, provenance, and tokenizer verification pass.

**Source list reported by the real archive scan:** securelist 337; asec 124; volexity 63; unit42 39; sentinellabs 38; trendmicro 30; talos 22; groupib 15; bitdefender 8. Other candidates fall below eight. This evidence comes from user-executed real staging, not independently rescanned on this server.

CPU checks distinguish two fixtures: the retained legacy 10-source/7,680-call synthetic replay and a new actual-protocol 9-source/6,912-call complete synthetic scoring replay. Neither produces experimental evidence.
