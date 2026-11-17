# Human-labelled subset

Adds a bounded accuracy view to the decision-sensitivity study: are the extra
example-driven selections under NF4 relevant or irrelevant sentences?

## Design (fixed before labelling)

- 36 windows = 9 publishers × 4 reports × 1 window; 288 target sentences.
- Selected by `select_subset.py` with the fixed salt
  `ThreatStudy-v2.3-human-annotation-subset-2026-11-13`, using identifiers only.
  Model outputs are never read during selection or sheet creation.
- Two independent annotators, blind to model outputs and to each other,
  label each TARGET sentence 1/0 using the models' frozen relevance definition
  ([GUIDELINES.md](GUIDELINES.md)). Disagreements are adjudicated jointly.

## Steps

```bash
# 1. author only: build blinded sheets (needs the original inputs.jsonl, not distributed)
python3 annotation/make_annotation_sheet.py --inputs /path/to/inputs.jsonl --annotators A B
# 2. each annotator fills column `relevant` (1/0); return the files as labels/A.xlsx, labels/B.xlsx
# 3. agreement + disagreement list
python3 annotation/analyze_annotation.py --labels annotation/labels/A.xlsx annotation/labels/B.xlsx --out results_rerun/annotation
# 4. adjudicate disagreements into labels/adjudication.csv (item_id,relevant), then rerun with --adjudication
```

`--selftest` runs the full pipeline on random synthetic labels to check the code;
its output is marked `SYNTHETIC_SELFTEST_NOT_RESULTS` and must never be reported.

## Analyses produced

- Cohen's kappa and raw agreement (pre-adjudication).
- Decision quality per arm × model × precision: precision/recall/F1 (Arms A, B),
  top-1 relevance (Arm C), with descriptive publisher-cluster bootstrap CIs.
- The example-index interaction recomputed separately on gold-relevant and
  gold-irrelevant targets (NF4 − BF16, exact publisher sign-flip p).
- BF16→NF4 decision changes split by gold label and by on-/off-example position:
  do NF4's added selections add false positives or recover true positives?

## AI-generated reference labels (exploratory, added after all results)

`ai_labels/ai_labels_by_slot.csv` holds labels produced by **one LLM
(Anthropic `claude-fable-5-2`) in a single pass** for all 1,152 target slots,
keyed by `window_id` and `target_index`. They are **AI-generated, not human
judgements, not adjudicated and not ground truth**. They contain no report text;
the annotator's evidence notes (which paraphrase report text) are not released.

- `build_ai_slot_labels.py` (author only): links the blinded AI items to slots by
  exact sentence text and checks that the link is lossless for labels.
- `analyze_ai_labels.py`: decision quality (P/R/F1, top-1 relevance), the
  label-stratified NF4−BF16 interaction, BF16→NF4 change decomposition and
  sensitivity analyses. Standard library only; writes `results/ai_labels/`.
- `ai_labels/run_metadata_claude-fable-5-2.json`, `ai_labels/validation_report_claude-fable-5-2.md`:
  the annotator's own run record and integrity checks.

```bash
python3 annotation/analyze_ai_labels.py   # ~20 s
```

## Human labels (two experts) and consensus labels

`human_labels/human_labels_by_slot.csv` holds, for every target slot whose sentence
belongs to the 288-item human subset, the labels of annotator H1 (15 years,
public-sector cybersecurity), annotator H2 (10 years, private-sector
cybersecurity) and the AI annotator, the adjudicated expert label (`adjudicated`, primary),
the three-rater majority label (`label`; U abstains) and the H1–H2 agreement label (`h_agree`). No text and no
justifications are included. `human_labels/agreement.json` holds Cohen's and
Fleiss' kappa and related counts.

Annotators are not named, for their privacy. They worked alone, did not see each
other's labels or the AI labels, and used no AI tools.

Deviations from the plan above: the experts labelled a separate publisher-stratified
draw made when the annotation kit was built (four reports per publisher by SHA-256
ranking, one window each, 36 windows, 288 items; membership verified against the
private identifier map, but the ranking-key serialisation was not preserved), not the
windows listed by `select_subset.py`, and used the kit's 1/0/U scheme. H1 and H2 then
jointly adjudicated all 100 items on which they had not given the same 0/1 label,
using a private workbook built by `make_adjudication_sheet.py` (the two experts' own
labels and notes only; no AI labels or model outputs). `build_human_slot_labels.py
--adjudication <file>` adds the `adjudicated` column, which is the primary label; the
three-rater majority (`label`), `h_agree` and each rater alone are sensitivity analyses.
`human_labels/agreement.json` records how the disputed items were resolved.

The instruction given to the AI annotator is in `ai_labels/PROMPT_claude-fable-5-2.txt`. Labels are attached at sentence
level, so repeated boilerplate sentences label additional slots (371 in total).

```bash
# author only (needs the private sheets and inputs.jsonl):
python3 annotation/build_human_slot_labels.py --inputs inputs.jsonl --a1 a1.csv --a2 a2.csv --ai AI_FULL_1152_ANNOTATED.csv \
    --adjudication ADJUDICATION_H1_H2.xlsx
# anyone:
for c in adjudicated label h_agree a1 a2 ai; do
  python3 annotation/analyze_ai_labels.py --labels annotation/human_labels/human_labels_by_slot.csv \
      --label-column $c --partial --out results/human_labels/$c
done
```

## Original annotation slots (primary human-label analysis)

`analyze_original_slots.py` restricts the human-label analysis to the 288 slots the
experts were actually shown (36 windows x 8 targets), each labelled once, instead of
copying each sentence label to every slot that carries the same sentence (371 slots).
The private item-to-slot key is not needed: 32 windows are identified uniquely by
their sentence texts, and the other four come from two classes of text-identical
windows (one securelist window with 2 copies, one Group-IB window with 8 copies; the
draw contains 1 and 3 of them). The released decisions are identical across copies in
every arm, model, precision and example index, so every result is the same whichever
copies are taken. `human_labels/draw_windows.csv` lists one such choice.

Checks the script runs (it stops if any fails):

- the released decisions agree across all text-identical copies;
- Cohen's kappa in `human_labels/agreement.json` reproduces from the slot labels of the draw;
- the E1 protocol's human-reference F1 guardrail, computed author-side with the private
  key (`extensions/E5_synthesis/evidence/E1_cell_quality.csv`, `E1_F1_interaction_DID.csv`),
  reproduces exactly on the recovered draw (12 confusion tables, 3 difference-in-differences);
- author only (`--a1 <private item sheet>`): every 36-window set whose sentence hashes equal
  the 288 item hashes is the listed draw up to swapping copies.

```bash
python3 annotation/analyze_original_slots.py      # ~20 s, standard library
```

Outputs in `results/human_labels_original/`: `draw288/<label set>/` (primary; label sets
adjudicated, h_agree, a1, a2, label, ai), `distinct/<label set>/` (the three identical
Group-IB windows counted once), `effective_sample_size.json` (labelled slots, distinct
sentences and Kish effective n for the original, distinct and expanded slot sets) and
`e1_guardrail.json`. The expanded 371-slot analysis remains in `results/human_labels/`
as a sensitivity analysis.
