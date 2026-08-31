# Reference vs Ours

**REFERENCE_RESULT**, **OUR_RESULT** (L0/L1/L2/L3), and **REPRODUCTION_RESULT** are
never mixed in this document (`evaluation/result_kind.py`). Nothing here is a
`REPRODUCTION_RESULT` — official ChildAgentEval access was never received, so no true
reproduction exists. Everything under "Our L0-L3" is an `OUR_RESULT` from the
Independent Interactive Cognitive-Age Benchmark, not ChildAgentEval.

## What the reference paper reported

**REFERENCE_RESULT.** Qwen3.5-27B baseline total composite score (paper's own
proprietary scale, medium confidence per `reference/reference_results.json` — cross-
verified across two independent extraction passes): age 7 = 0.32, age 10 = 0.34,
age 13 = 0.29, age 16 = 0.30.

## What our L0 actually produced

**OUR_RESULT.** Independent-benchmark binary accuracy (8 original tasks per age, one
per category): age 7 = 0.625 (5/8), age 10 = 0.500 (4/8), age 13 = 0.500 (4/8),
age 16 = 0.625 (5/8). Overall: 18/32 (0.5625).

## What changed under L1/L2/L3

**OUR_RESULT.** Nothing, on the accuracy dimension: L1, L2, and L3 each produced
exactly 18/32 (0.5625), with the identical per-task pattern as L0 (all 32 tasks'
correct/incorrect outcomes matched L0 exactly in every condition). L3 changed
trajectory efficiency — 143 vs 152 total steps, 98,318 vs 105,073 tokens, $0.021981 vs
$0.023440 — via 70 interventions (48.95% of its steps), with zero accuracy cost. L1 and
L2 recorded zero interventions.

## Statistical evidence

Paired comparison (n=32 tasks): L0 vs L1 mean difference = 0.000 (p=1.000); L0 vs L2
mean difference = 0.000 (p=1.000); L0 vs L3 mean difference = 0.000 (p=1.000). Every
one of the 32 per-task score differences is exactly zero in all three comparisons —
there is no sampling variance for Cohen's d to be computed from. N is never hidden: all
comparisons are explicitly n=32.

Reference-vs-L0 "difference" (age 7: +0.305, age 10: +0.160, age 13: +0.210,
age 16: +0.325) is **not** a statistical comparison — the reference and our L0 use
different, non-commensurable scoring systems (see below), so no significance test was
run on it, and none should be.

## Interpretation

**[INTERPRETATION]** Within this run, none of the three guardrails changed which
answer Qwen3.5-27B ultimately submitted on any of the 32 tasks. L3's substantial
intervention rate changed *how* the model got to its answers (fewer redundant/looping
steps) without changing *what* answer it submitted. **[INTERPRETATION]** The
reference-vs-L0 gap is uninterpretable as a claim about relative model capability,
since the two numbers come from unrelated item sets, scoring rubrics, and (per Phase 0)
an entirely undisclosed official methodology — the gap could reflect item difficulty
differences, scoring-scale differences, or genuine capability differences, and this
data cannot distinguish between those possibilities.

## Limitations

- The reference values themselves are the paper's own numbers, not independently
  re-derived — see `reference/README.md` for their confidence provenance.
- Our L0 accuracy and the paper's composite score are not on the same scale, may not
  weight subtests/categories the same way, and are not proven to measure the same
  underlying construct.
- No claim of reproduction, validation, or invalidation of the original
  ChildAgentEval result is made anywhere in this document.
