# Annotation guidelines: CTI sentence relevance (v2.3 labeled subset)

## Purpose

The study measures whether low-precision (NF4) models change *which* sentences
they select as relevant when only the demonstrated output-example index changes.
These labels let us ask whether the extra example-driven selections land on
sentences that a human analyst considers relevant or irrelevant. The labels are
**not** used to tune anything; the subset was fixed before any labels existed
(`select_subset.py`, fixed salt) and without looking at model outputs.

## Your task

For each numbered **TARGET** sentence, decide independently:

> **1 = relevant** if the TARGET sentence itself describes actionable cyber-threat
> intelligence: adversary behaviour, attack methods, technical attack
> infrastructure, or concrete threat evidence.
> **0 = not relevant** otherwise, including sentences that mention cybersecurity
> only generically.

This is the same definition the models received (frozen in
`src/v216_inference/crosscti/core.py`). Use the `context_before` text only to
understand the TARGET; never label the context itself.

## Decision rules

Label **1** when the TARGET contains at least one of:

1. **Adversary behaviour or method.** What the actor did or does, e.g. "The
   loader injects the payload into a suspended svchost process."
2. **Technical infrastructure or indicators.** C2 domains or IPs, URLs, file
   hashes, file paths, registry keys, mutexes or certificates *used in the attack*,
   even when defanged (`hxxp`, `[.]`).
3. **Malware or tool capability.** Specific functionality of the malicious code
   or of the attacker's tooling.
4. **Concrete threat evidence.** Observed targeting, victims, exploited CVEs,
   attribution evidence or campaign timing that is specific to this threat.

Label **0** when the TARGET is:

- generic security advice, marketing or product text ("Our platform protects…");
- a heading, a navigation fragment, a figure caption without technical content,
  or boilerplate ("Read more", "Table 2", "Update:");
- a general statement about the threat landscape that has no specific behaviour,
  infrastructure or evidence;
- a description of the *defender's* product, detection name or research process,
  with no information about the threat itself.

## Edge cases

- **Mixed sentences.** If any clause meets a rule above, label 1.
- **Detection names** (e.g. `Trojan.Win32.X`): 1 only if the sentence also states
  what the threat does or where it was seen; a bare detection list is 0.
- **Attribution claims:** 1 if they cite evidence (shared code, infrastructure,
  TTP overlap), 0 if purely speculative.
- **Victimology:** 1 if specific (sector, region or organisation targeted in
  this campaign), 0 if generic ("organisations worldwide").
- **Truncated or garbled text:** judge what is readable. If you cannot judge,
  set `unsure = Y` and give your best label anyway.

## Procedure

1. Work alone. Do not discuss items with the other annotator until both sheets
   are complete.
2. Do not look at model outputs, results files or the other annotator's sheet.
3. Fill `relevant` with **1 or 0** for every row. `unsure` (Y/blank) and `note`
   are optional.
4. Expected effort: about 2 hours for 288 sentences. Take breaks between windows.
5. Return the file unchanged apart from the three answer columns.

## After both sheets are complete

The study author runs `annotation/analyze_annotation.py`. It reports
Cohen's kappa and lists disagreements for joint adjudication. Adjudicated labels
go into `labels/adjudication.csv` (columns `item_id,relevant`). Report both the
pre-adjudication agreement and the adjudicated gold standard.
