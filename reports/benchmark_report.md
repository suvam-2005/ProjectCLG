# Benchmark Report — Independent Interactive Cognitive-Age Benchmark, L0-L3

Frozen at git commit `849542ba9768e4e1297a735f56bd03ad0c6e84f4`. Full raw data:
`data/independent_benchmark/raw/`. This benchmark is **NOT ChildAgentEval** and is not
claimed to be numerically equivalent to it.

Throughout: **[OBSERVATION]** = a directly measured fact. **[INTERPRETATION]** = a
reasoned reading of observations, still fairly grounded. **[HYPOTHESIS]** = a
speculative explanation not established by this run's evidence alone.

## 1. Abstract

We evaluated whether three cognitive guardrails (output-level, action-level, dynamic
trajectory-level) change the behavior of Qwen3.5-27B on an original, 32-task
interactive cognitive-age benchmark, relative to a no-guardrail baseline (L0). **[OBSERVATION]**
Task accuracy was identical across all four conditions (18/32, 56.25%), and per-task
correctness was identical for all 32 tasks in every condition — the same tasks
succeeded and failed regardless of guardrail. The dynamic guardrail (L3) intervened on
70 of 143 steps (48.95%) and reduced total steps/tokens/cost by ~6%, with zero change
to any measured outcome. The output (L1) and action (L2) guardrails never intervened.

## 2. Research question

Can external cognitive guardrails improve cognitive-age alignment in Qwen3.5-27B while
preserving task capability? **[OBSERVATION]** In this run: no guardrail changed
measured alignment or capability at all; L3 changed trajectory efficiency without
changing outcomes.

## 3. Reference study

"Evaluating Cognitive Age Alignment in Interactive AI Agents" (arXiv:2605.17894,
PediaMedAI/ChildAgentEval). Used only as methodological inspiration and for four
contextual reference data points (§14, §18.4 confirmed values). See
`docs/phase0_findings.md`.

## 4. Why an independent benchmark was necessary

Official ChildAgentEval access was never received (Phase 5 access-gate check). Per
explicit instruction, no attempt was made to reconstruct or reproduce ChildAgentEval —
this is an original benchmark informed only by publicly described cognitive/interaction
categories. See `docs/independent_benchmark_specification.md`.

## 5. Benchmark methodology

32 original task instances: 8 categories x 4 anchor ages (7, 10, 13, 16) x 1 task each,
reused identically across L0-L3 (guardrail fairness). Two interaction kinds
(`multiple_choice`, `sequence_click`), deterministic post-hoc scoring that never exposes
the answer to the agent. Full spec: `docs/independent_benchmark_specification.md`.
Frozen: `configs/experiments/final_benchmark.yaml`.

## 6. Task design

Categories: working_memory, reasoning, abstraction, language, visual_spatial,
planning, processing_behavior, integrated_reasoning (`INDEPENDENT_BENCHMARK_DIMENSIONS`).
Difficulty scales with age within each category (e.g. working_memory sequence length
6→7→8→9 items from age 7→16). All content is original; validated end-to-end against
real Chromium before use (Phase 5C found and fixed a real environment bug —
`available_elements` was never populated, which would have made every real click fail
silently — caught in a pre-flight check before any paid run).

## 7. Model configuration

`qwen/qwen3.5-27b` via OpenRouter, temperature 0, max_output_tokens 256,
`response_format: json_object`, `reasoning: {enabled: false}` — identical across all
four conditions.

## 8. Experimental conditions

- **L0**: no guardrail (`NoGuardrail`)
- **L1**: output guardrail (`L1-v1`) — inspects raw model text, allows/modifies/rejects
- **L2**: action guardrail (`L2-v1`) — inspects parsed action against the agent's own
  observation, rejects premature finish / invalid targets
- **L3**: dynamic guardrail (`L3-v1`) — monitors trajectory history, substitutes `wait`
  for repeated actions, forces `finish` after 5 steps without completion

Implementation: `src/childagenteval_research/guardrails/`.

## 9. Budget

Combined benchmark spend (all 4 conditions + both pilots): **$0.110330**. Remaining of
the $8 cap: **$7.889670**. Total project ledger: **$0.110349** (704 API calls). Never
approached the $6.50 soft limit or $8 hard limit at any point.

## 10. L0 results

32/32 tasks. **[OBSERVATION]** 18/32 correct (56.25%). Per age: 7→5/8, 10→4/8, 13→4/8,
16→5/8. Per category: abstraction/integrated_reasoning/language/processing_behavior =
4/4; visual_spatial = 2/4; planning/reasoning/working_memory = 0/4. 152 total steps,
105,073 tokens, $0.023440, 2 malformed-output events (both recovered, scoring-neutral).
One external process interruption during this condition, resumed per documented policy
(`data/independent_benchmark/L0_retry_log.md`).

## 11. L1 results

32/32 tasks. **[OBSERVATION]** Identical to L0 on every dimension: 18/32 correct, same
per-age and per-category breakdown, same 152 steps, 0 interventions. Two transient
network errors (unrelated to the guardrail), resolved by single-task retries.

## 12. L2 results

32/32 tasks. **[OBSERVATION]** Identical to L0/L1: 18/32 correct, same breakdowns, same
152 steps, 0 interventions. One external process interruption, resumed per policy.

## 13. L3 results

32/32 tasks. **[OBSERVATION]** 18/32 correct — same count AND same per-task
correctness as L0/L1/L2 (verified: all 32 task outcomes identical to L0). 143 total
steps (−9 vs L0, −5.9%), 98,318 tokens (−6.4%), $0.021981 (−6.2%). **70 interventions**
across 143 steps (48.95% intervention rate) — every other condition had zero. One
transient network error, resolved by retry; one external process interruption during
the working_memory batch, resumed per policy.

## 14. Reference vs L0

| Age | Reference (paper) | Our L0 | "Difference" |
|---:|---:|---:|---:|
| 7 | 0.32 | 0.625 | 0.305 |
| 10 | 0.34 | 0.500 | 0.160 |
| 13 | 0.29 | 0.500 | 0.210 |
| 16 | 0.30 | 0.625 | 0.325 |

**Reference contextual comparison — metrics are not assumed equivalent.** The
reference is the paper's proprietary composite score on unpublished, WISC-derived
items; ours is binary accuracy on 8 original items per age on an unrelated task set.
The "Difference" column is arithmetic only, not a statistically or substantively
meaningful comparison. See `docs/independent_benchmark_specification.md` §1 for why
this benchmark exists at all. Full detail: `reports/reference_vs_ours.md`.

## 15. Alignment analysis

**[OBSERVATION]** Condition-level alignment (mean of 4 per-age alignment scores,
`independent_alignment.py` formula): L0 = L1 = L2 = L3 = **0.51875** exactly. Per-age:
7→0.4625, 10→0.5, 13→0.5, 16→0.6125, identical across all 4 conditions. This follows
directly from identical per-category accuracy across conditions (§10-13) — alignment is
computed from category scores, which never differed.

## 16. Capability analysis

**[OBSERVATION]** Task capability (mean binary score over 32 tasks) = **0.5625** for
all four conditions, exactly. **[INTERPRETATION]** No guardrail measurably helped or
hurt task capability in this run.

## 17. Alignment-capability tradeoff

| Condition | Alignment | Capability | Alignment gain vs L0 | Capability change vs L0 | Capability retention vs L0 |
|---|---:|---:|---:|---:|---:|
| L0 | 0.51875 | 0.5625 | 0.000 | 0.000 | 1.000 |
| L1 | 0.51875 | 0.5625 | 0.000 | 0.000 | 1.000 |
| L2 | 0.51875 | 0.5625 | 0.000 | 0.000 | 1.000 |
| L3 | 0.51875 | 0.5625 | 0.000 | 0.000 | 1.000 |

**[OBSERVATION]** All four conditions occupy the exact same point in
alignment-capability space (Figure 5 shows all 4 labels overlapping at one point) —
there is no tradeoff to report because there was no change on either axis.

## 18. Per-age analysis

Identical across all 4 conditions (Figure 6): age 7 → 5/8 (0.625); age 10 → 4/8 (0.5);
age 13 → 4/8 (0.5); age 16 → 5/8 (0.625). **[OBSERVATION]** Non-monotonic with age (a
dip at 10-13, not a steady increase) — a valid result, not evidence of a broken metric.

## 19. Per-category analysis

Identical across all 4 conditions (Figure 7): abstraction, integrated_reasoning,
language, processing_behavior all 4/4; visual_spatial 2/4; planning, reasoning,
working_memory all 0/4. **[OBSERVATION]** The three 0/4 categories are exactly the
categories requiring either multi-step exact-sequence reproduction (planning,
working_memory, both `sequence_click`) or numeric pattern extrapolation (reasoning).
**[HYPOTHESIS]** These may be harder for this model under this prompt/action-schema
design specifically, rather than reflecting a general incapability — not established by
this run alone (n=4 tasks per category is too small to generalize, and no ablation
isolating task format from content was run).

## 20. Intervention analysis

L0/L1/L2: 0 interventions. L3: 70 interventions across 143 steps (48.95%). **[OBSERVATION]**
L3's `EXCESSIVE_STEPS_THRESHOLD=5` rule fired on multiple tasks with `maximum_steps > 5`
— e.g. `planning_age13_v1`/`planning_age16_v1` completed in 6 steps under L3 vs 7/8
under L0-L2, and all 4 working_memory tasks completed in exactly 6 steps under L3 vs
6/7/8/9 under L0-L2. `unnecessary_intervention_rate` was not computed — no independent
post-hoc evaluator exists for this benchmark (see `intervention_metrics.py`;
fabricating one was avoided per the brief).

## 21. Error/recovery analysis

| Condition | Errors | Recoveries |
|---|---:|---:|
| L0 | 2 | 2 |
| L1 | 2 | 2 |
| L2 | 1 | 1 |
| L3 | 2 | 2 |

All are the same "bare JSON scalar" malformed-output pattern investigated and
partially mitigated in Phase 5C (a schema-instruction fix reduced but did not
eliminate the failure mode — see `docs/phase5c_pilot_reliability_and_freeze.md`).
**[OBSERVATION]** Every recovered task still scored the same as it would have without
the malformed step (recovery is scoring-neutral, as established in the pilot and
reconfirmed here by the fact that per-task outcomes never differ from L0).

## 22. Token/cost analysis

See Table 8 (`reports/tables.md`) and Figure 10. **[OBSERVATION]** L3 is the only
condition with materially different token/cost usage (~6% lower), directly attributable
to its intervention-driven early terminations.

## 23. Statistical analysis

Paired comparison (same 32 tasks) L0 vs L1/L2/L3: mean difference = 0.000 exactly for
all three, Welch's t = 0.000, p = 1.000, Cohen's d undefined (zero variance in
differences — every one of the 32 per-task score differences is exactly 0). **[OBSERVATION]**
This is not "no significant difference" in the usual noisy-data sense — the underlying
per-task outcomes are byte-for-byte identical across conditions, so there is no
variance for a significance test to operate on. N=32 tasks, reported per the brief's
requirement to never hide N. No multiple-comparison correction was needed (all
comparisons already show exactly zero effect).

## 24. Limitations

- This is an original benchmark, not ChildAgentEval — no claim of equivalence to any
  official result (§14).
- 32 tasks (1 per category per age) is a modest sample; per-category N=4 and per-age
  N=8 limit statistical power to detect anything but very large effects.
- The independent alignment metric (`independent_alignment.py`) is our own documented,
  validated-on-synthetic-data formula — not a claim of equivalence to any clinical or
  official psychometric alignment measure.
- Failure-category classification (Table 7) was not run this phase.
- No repeated runs (temperature=0, single run per condition) — cannot separate
  measurement noise from true determinism; the near-total identity of results across
  conditions is consistent with (but doesn't prove) high determinism at temperature 0.

## 25. Threats to validity

- **Construct validity**: our 8 categories are informed by, but not validated against,
  any official cognitive taxonomy.
- **Internal validity**: L3's interventions changed trajectories (fewer steps) without
  changing final answers — plausible given scoring only reads the last click/full
  sequence, but this means L3's benefit (efficiency) and its null effect (no capability
  change) are both partly an artifact of this specific scoring design, not necessarily
  generalizable to a benchmark that penalizes trajectory length directly.
- **External validity**: single model (Qwen3.5-27B), single temperature (0), single run
  — results may not generalize to other models, temperatures, or repeated sampling.
- **Guardrail scope**: L1/L2 never triggered in this run; their true effect (if any) is
  untested here, not disproven — the honest conclusion is "no evidence of an effect
  under these specific 32 tasks," not "these guardrails don't work."

## 26. Reproducibility

Frozen config `configs/experiments/final_benchmark.yaml`, git commit
`849542ba9768e4e1297a735f56bd03ad0c6e84f4`, task-set SHA-256
`4e6ae6752b69bae171fe56f2918ec7c8b773f00d5581824d89747e87afe73df8`. Full manifest:
`reports/reproducibility_manifest.json`. Every result traces: raw trajectory
(`data/independent_benchmark/raw/trajectories/`) → task result
(`data/independent_benchmark/raw/{condition}.jsonl`) → processed aggregate
(`data/independent_benchmark/processed/`) → statistics
(`data/independent_benchmark/statistics/`) → figure/table (`reports/figures/`,
`reports/tables.md`) → this report. No manually edited numbers.

## 27. Conclusion

**[OBSERVATION]** Under this specific 32-task benchmark, L1 and L2 had no measurable
effect on Qwen3.5-27B's behavior (zero interventions, identical outcomes to L0). L3
intervened extensively (48.95% of steps) and reduced trajectory length/tokens/cost by
~6%, while leaving task accuracy and cognitive alignment completely unchanged.
**[INTERPRETATION]** This is a genuine, if narrow, positive efficiency result for the
dynamic guardrail approach specifically — capability was fully preserved under heavy
intervention. **[HYPOTHESIS]** Whether this generalizes to a benchmark where trajectory
length itself affects scoring, or to guardrail conditions that actually change which
answer gets submitted, is not established by this run and would require a different
task design to test.
