**v2.0.2 PROVENANCE UPDATE:** The CTINexus GitHub JSON archive was audited: 298 files, 148 unique texts, **zero publisher labels**. The originally proposed publisher-level confirmatory experiment cannot be supported from that archive. Treat all text below as a historical proposal, not a validated external-corpus dataset. See `CPU_VALIDATION_REPORT.md`.

---

# Frozen scientific decision log (v2.0)

- Motivation: v1.5.1 result on 40 reports/5 sources produced positive NF4-minus-BF16 effect under two demonstration indices, with source-exact p=0.0625 each; near-zero literal `[0]` to `[4]` copying and large selection-set inflation undermine the simplistic copying mechanism.
- Corrective strategy: 8 demonstrations each containing distinct zero-based index 0...7, all same length; all eight prompts on identical input; report-level paired data; equal source weights.
- External dataset intended: CTINexus. Its publisher diversity is reported, not independently confirmed in this environment. The underlying annotation task differs, so reject direct false-positive/F1 comparisons.
- Sample locked before model outputs: 8 reports × 10 sources × 2 windows/report = 160 windows, all eight prompts; 7,680 calls; three pinned model families BF16/NF4.
- Primary: balanced anchor association as formula in README, precision interaction, publisher-level exact sign flip and Holm correction. Sensitivity and cardinality diagnostics distinct.
- Invalidation: source fields absent, fewer than 10 publishers, fewer than 8 qualifying reports per publisher, ambiguous format, source text provenance unverified, real tokenizer unequal prompt lengths, dataset checkpoint drift, checkpoint hash mismatch, or undisclosed duplication with prior corpus.
- Completion claim: CPU software simulation PASS; real dataset prep, model tokenizer gate and real GPU inference NOT RUN.
