# Validation report — ThreatStudy v2.2.1 AI annotation pass

**All labels in this package are AI-generated annotations (model `claude-fable-5-2`). They are not human judgments and not ground truth.**

Validated (UTC): 2026-11-13T17:34:59+00:00  
Overall result: **PASS**

## Integrity checks

| Check | Result |
|---|---|
| input_rows | 1152 |
| output_rows | 1152 |
| output_header_matches_required_schema | True |
| missing_ids | 0 |
| unexpected_ids | 0 |
| duplicate_ids | 0 |
| row_order_preserved | True |
| source_text_unchanged | True |
| invalid_label | 0 |
| invalid_category | 0 |
| invalid_confidence | 0 |
| incomplete_records | 0 |
| U_without_explanation | 0 |
| batch_sizes | [64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64] |
| batch_sizes_within_32_64 | True |
| unique_target_sentences | 1027 |
| identical_text_groups_with_conflicting_labels | 0 |
| context_before_nonempty_rows | 0 |

List-valued checks show the number of offending IDs (0 = none).

## Label distribution

| Label | n |
|---|---|
| 1 | 445 (38.6%) |
| 0 | 690 (59.9%) |
| U | 17 (1.5%) |

| Category | n |
|---|---|
| not_actionable | 690 (59.9%) |
| attack_method | 177 (15.4%) |
| adversary_behavior | 124 (10.8%) |
| threat_evidence | 94 (8.2%) |
| other_specific | 29 (2.5%) |
| infrastructure | 21 (1.8%) |
| uncertain | 17 (1.5%) |

| Confidence | n |
|---|---|
| high | 645 (56.0%) |
| medium | 294 (25.5%) |
| low | 213 (18.5%) |

| Label × confidence | n |
|---|---|
| 0|high | 515 |
| 0|low | 52 |
| 0|medium | 123 |
| 1|high | 130 |
| 1|low | 144 |
| 1|medium | 171 |
| U|low | 17 |

## Not checked

- Per-publisher / per-report counts: these need `PRIVATE_ID_MAP...csv`, which the annotator did not open. Run that breakdown on the analyst side.
- Agreement with human labels: no human labels exist yet; the two human files were not opened.
