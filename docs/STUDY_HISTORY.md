# Study history and disclosure

The final study is the v2.1.6 Arm A run plus the v2.2.1 Arms B/C. Earlier
phases are disclosed here because they shaped the final design. Their raw
archives are kept by the author and are available on request.

| Phase | Corpus | What was learned | Status in the paper |
|---|---|---|---|
| Pilot v0.1–v0.8 | PRISM (LANCE) IoC-annotated reports, 50 reports | BF16/NF4 extraction differences, but formatting and gold-label matching confounds; only 6 independent indicator-sharing groups in validation | Exploratory, not reported as evidence |
| v1.1–v1.2 | SMAH-CTI test partition, 20 reports | An output example containing `[0]` caused a strong position-0 fixation | Motivated the example-index question |
| v1.4.1–v1.5.1 | SMAH-CTI train partition, 40 reports, 284 windows, example 0 vs 4 | Positive NF4−BF16 interactions (+10.98, +12.32, +14.66 pp) but only 5 publisher groups (exact p = 0.0625 each; Holm 0.1875) | Underpowered at publisher level; motivated a 9-publisher corpus |
| CTINexus audit v2.0.1 | 298 annotation files | 148 unique texts and no usable publisher field | Rejected as a publisher-level corpus |
| v2.0–v2.1.5 | CTI-Crawler APT subset | 9 publishers × 8 reports; overlap repair removed 2 reports overlapping selected SMAH windows | Final corpus (frozen) |
| **v2.1.6** | 144 windows | **Arm A**: 6,912 calls, all 8 example indices balanced | **Primary result** |
| v2.2-Core (CPU) | synthetic + archived records | 256-subset grammar, synthetic replay, tokenizer alignment repair | Implementation validation |
| **v2.2.1** | same 144 windows | **Arms B and C** (6,912 calls each) + 432-call replay | **Mechanism extension** |

## Disclosures

1. **Post-hoc extension.** Arms B and C were designed after the Arm A results
   were known. They were frozen by a locally recorded SHA-256 amendment
   (`protocol/V221_FREEZE_AMENDMENT.md`) before any B/C inference, but they were
   not externally preregistered.
2. **Unexecuted draft.** `protocol/ARCHIVED_wider_v22_draft_NOT_EXECUTED.docx`
   proposed GPTQ, INT8 and Qwen-14B conditions; none of these were run.
3. **Execution order.** The frozen order was replay → Arm C → Arm B. New records
   were never mixed with earlier checkpoints.
4. **Gold labels.** The main study has no human relevance labels; see
   `annotation/` for the labelled subset added for the manuscript.
