# ThreatScope — E6 independent release-readiness assessment

**Verdict: Computationally ready for an additive GitHub release with disclosures; manuscript requires author integration and final editorial/rights review.**

## Pass

1. E5 replay verifies E1=1,728, E2=2,304, E3=3,456, E4=1,152 decision records.
2. E3/E4 raw checkpoint archives available, independently inspected and included with numerical exports.
3. Historical release remains byte-for-byte unchanged within its original files.
4. E3 input checksum and frozen selection count match the supplied gate, while actual private CTI source text is deliberately excluded.
5. E4 FP4 inference is a revisioned change from an earlier AWQ/GPTQ suggestion.

## Scientific cautions

* E1 frozen complete-case estimand differs from historical Arm A–C, and missing-output rules can reverse the Llama estimate.
* E2 scoring/greedy alternatives almost coincide at the token level, providing a procedure check rather than causal isolation.
* E3 is an eight-publisher report holdout from the **same** archive. Neither external-corpus nor temporal independence is shown.
* E4 FP4 vs NF4 differences did not pass family-wise adjusted tests and include malformed-output shifts.
* Human adjudication asymmetry and missing full contextual source text prevent calling the 288 items an undisputed expert ground truth.
* The original release contains archived labels and metadata. Public redistribution rights and privacy should be checked by the author.

## Missing evidence / limitations of this assembled release

* E1/E2 per-record decision tables are available, but their *complete original raw inference checkpoint bodies* were not provided for this E6 assembly.
* Original full 10.69 GB APT archive and private 72-report E3 input are not redistributed. Exact end-to-end neural inference and source provenance require the user's local corpus and pinned weights.
* Independent human annotation raw sheets and adjudication transcripts are not reproduced here.
* Manuscript PDF was not edited or formally accepted in this release package; `MANUSCRIPT_REVISION_INSERTIONS.md` is the author-editable change text.

## Release recommendation

Add `extensions/`, `README_EXTENSION_E6.md`, `MANUSCRIPT_REVISION_INSERTIONS.md`, `E6_READINESS_AUDIT.md`, and `verify_e6.py` to the existing repository on a new tag such as `v1.1.0-extension-evidence`. Do not alter or force-update v1.0.0. Confirm the final public URL after uploading. Keep `restricted` materials outside GitHub.
