# reference/

`reference_results.json` — every quantitative result extracted from the paper
(arXiv:2605.17894) via automated fetch-and-summarize tooling, each row tagged with
`result_kind: "reference_result"` (never mixed with our own measurements),
`confidence` (high/medium/low), and `status` (see
`src/childagenteval_research/evaluation/reference_results.py` and
`source_evidence.py`).

**Read the confidence/status field before using any row.** Only the four
Qwen3.5-27B baseline `total_composite_score` rows are `status: "confirmed"` (they were
reproduced identically across two independently-worded extraction passes over the
paper's HTML). Everything else is `status: "unverified_single_pass"` or worse — most
notably, a full per-subtest/per-factor breakdown table was extracted once and rejected
entirely (not included here) because it contained an internal contradiction (implausibly
high factor z-scores for a model whose own composite score was near the lowest of any
model tested), strongly suggesting the automated table parse mis-aligned columns.

This is not a substitute for reading the actual PDF or obtaining author access — see
`docs/phase4_reproduction_specification.md` for the full methodology and limitations.
