# Phase 3 — Evaluation + Metrics Framework

Date: 2026-08-24. Zero OpenRouter calls this phase. No Qwen, no ChildAgentEval, no
guardrail algorithms, no WISC-derived content. Everything below is a pure-Python
metrics/statistics/schema library exercised only with synthetic data.

Legend used throughout: **CONFIRMED FROM PAPER** (verified in Phase 0 against the
arXiv text or the repo), **PROVISIONAL DESIGN** (our own reasonable placeholder,
explicitly flagged for revision), **FUTURE RESEARCH** (interface exists, no
implementation yet, by design).

## 1. Research questions

Primary: *"Can external cognitive guardrails improve cognitive-age alignment in an
open-weight multimodal agent while preserving task capability?"* (as given) —
**CONFIRMED FROM PAPER** as the framing, since it mirrors the paper's own stated
motivation (developmental appropriateness vs. raw capability). The framework refuses to
collapse this into one scalar: every comparison utility (`comparisons.py`) reports task
performance and alignment as two separate `MetricComparison` objects, never combined
into a single "score."

## 2. Experimental conditions

`evaluation/conditions.py` — `ResearchCondition` enum: `R0_original_baseline`,
`R1_output_guardrail`, `R2_action_guardrail`, `R3_dynamic_guardrail`. **CONFIRMED FROM
PAPER/BRIEF** as the four conditions; **no algorithm exists for R1-R3** —
`IMPLEMENTED_CONDITIONS` currently contains only R0. `STANDARD_COMPARISONS` encodes the
five requested pairs (R0-vs-R1/R2/R3, R1-vs-R2, R2-vs-R3).

## 3. Metric groups

Five modules, one per group from the brief:

- `capability.py` — `TaskPerformanceResult` (raw/subtest score, completion,
  correctness, failure, reversal/discontinuation). **Every field defaults to None** —
  `source="benchmark_adapter"` documents that nothing here is computed independently of
  whatever the (future) official adapter reports.
- `profiles.py` + `alignment.py` — cognitive alignment (detailed in §4-5).
- `tradeoff.py` — capability-alignment tradeoff (§6).
- `intervention_metrics.py` — R1-R3 intervention accounting (§7).
- `trajectory_metrics.py`, `token_cost_metrics.py` — trajectory-shape and token/cost
  measurement (§8-9), independent of benchmark scoring.

## 4. Cognitive profile representation

`profiles.py` — `CognitiveProfile.values: dict[str, ProfileValue]`, not a fixed set of
dataclass fields, so dimensions can be corrected later without a schema migration.
`PROVISIONAL_COGNITIVE_DIMENSIONS = (reasoning, working_memory, abstraction, language,
visual_reasoning, planning, processing_behavior)` — **PROVISIONAL DESIGN**, inferred
from the paper's CHC-factor groupings (Gc/Gf/Gv/WM/PSI) but not confirmed against the
actual methodology (Phase 0: unavailable). `ProfileValue` supports all four requested
representations — categorical, normalized score, distribution, confidence interval —
validated at construction (`__post_init__` requires the field matching `kind` to be
set). `TargetProfile`/`ObservedProfile` are thin, distinctly-named subclasses.

## 5. Alignment measurement

`alignment.py` — `AlignmentDistanceMethod` enum lists five candidates (Euclidean,
cosine, Mahalanobis, distributional, learned-representation). **Euclidean and cosine
are implemented** as raw measurements over whatever `NORMALIZED_SCORE`-kind dimensions
both profiles share; dimensions in other representations are skipped, not force-cast.
Mahalanobis/distributional/learned-representation are declared in the enum but
**raise `NotImplementedError`** — **FUTURE RESEARCH**, since they'd need
covariance/reference data this project doesn't have yet. No method is marked "the"
final metric. `compute_alignment()` also returns a per-dimension `1 - |target -
observed|` convenience score — explicitly documented as a provisional convenience, not
an official metric — plus `overall_alignment` as its mean. When no comparable
dimensions exist, results are `None`, never a fabricated 0 or 1.

## 6. Capability measurement

`tradeoff.py` implements exactly the four raw measurements requested — no composite is
asserted as correct:

- `alignment_gain(condition, baseline)` = condition − baseline
- `capability_change(condition, baseline)` = condition − baseline
- `relative_capability_retention` = condition / baseline, **`None` when baseline is 0**
  (not 0, not inf — that ratio is genuinely undefined)
- `alignment_per_capability_loss` — only defined when capability actually decreased
  (`capability_change < 0`); `None` otherwise, so it can never imply a "loss" that
  didn't happen

## 7. Intervention measurement

`intervention_metrics.py` — `InterventionEvent` (per-opportunity record) and
`InterventionSummary` (count, opportunities, accepted/rejected/modified/replan counts,
latencies, `intervention_rate` property). `unnecessary_intervention_rate()` **requires
an explicit `posthoc_evaluator` callback and returns `None` without one** — per the
brief's "do not fabricate labels," there is no default evaluator and none is invented.

## 8. Trajectory measurement

`trajectory_metrics.py` operates on the same dict shape `TrajectoryWriter.read_all()`
produces (Phase 2's real schema, not a new one). Implemented: total/successful/failed/
recovery steps, repeated-actions (consecutive identical final-action key), action
diversity (distinct actions / n), completion time (last − first timestamp), mean action
latency. **`unnecessary_actions` is always `None`** — this project does not have
benchmark-specific "optimal path" knowledge to judge necessity, and the brief forbids
inventing scoring formulas, so this is left honestly unknown rather than guessed.
`page_revisits` is `None` unless URL metadata is actually present in the observation
(only true for the Playwright adapter today). **PROVISIONAL DESIGN**: "action latency"
and "observation-to-action latency" currently resolve to the same measured quantity
(model decision latency) because this project doesn't separately time environment-side
execution yet.

## 9. Cost measurement

`token_cost_metrics.py` sums `input_tokens`/`output_tokens`/`cost_usd` directly from
trajectory records — all of which trace back to OpenRouter's real `usage` field
(`openrouter_client.py`), never an estimate, matching "cost must always be read from
actual usage when available." `cumulative_project_cost_usd` is an explicit passthrough
parameter the caller must supply from the real `CostGuard` ledger — this module never
recomputes a project total from a possibly-partial set of records.

## 10. Statistical framework

`statistics_utils.py` (pure standard library, no numpy/scipy): `describe()`
(mean/median/stdev/min/max, **always carries `n`**), `confidence_interval()`
(normal-approximation, explicitly documented as an approximation for small n, `None`
below n=2), `bootstrap_confidence_interval()` (seeded, reproducible), `effect_size()`
(Cohen's d, `None` below n=2 per side or zero pooled SD), `paired_comparison()`,
`spearman_rank_correlation()` / `kendalls_tau()` / `rank_correlation()`,
`bonferroni_correction()` / `benjamini_hochberg_correction()` (both report
`n_comparisons` and per-hypothesis `reject_null`). No function auto-applies a
significance test — everything returns `n` for the caller to judge.

## 11. Age analysis

Two distinct concepts, per `age_conditions.py`: **`BASELINE_ANCHOR_AGES = (7, 10, 13,
16)`** — **CONFIRMED FROM PAPER**; **`SKILL_GUIDED_AGE_BANDS = ("6-8","9-11","12-14",
"15-17")`** — **CONFIRMED FROM PAPER**, for the skill-guided condition only.
`validate_anchor_age()`/`validate_age_band()` raise `AgeConditionMismatchError` rather
than silently accepting an invented age or mixing the two schemes. `per_age_analysis.py`
groups results into `{age: {condition: [...]}}` and only summarizes within each cell —
ages are never averaged together before inspection. `age_trend_analysis.py` computes
Spearman/Kendall correlation for age-ordered scores; `monotonic_regression()` is an
explicit `NotImplementedError` stub — **FUTURE RESEARCH**, deliberately not choosing an
isotonic-regression implementation before the real score distribution is known.

## 12. Ablation framework

`ablation.py` — `R3AblationVariant` enum with the six requested variants (full, and
five "without X control" leave-one-out variants). `IMPLEMENTED_ABLATIONS` is an empty
frozenset — **FUTURE RESEARCH**, since R3 itself doesn't exist yet. Existing
`comparisons.py` machinery is generic enough to compare ablation variants once they
produce `ConditionResults`, without new comparison code.

## 13. Train/validation/test separation

`splits.py` — `DatasetSplit` enum (development/validation/test) and `SplitProvider`
protocol. **`NullSplitProvider` is the current default and always returns `None`** —
**CONFIRMED FROM PAPER (absence)**: Phase 0 found no evidence the official benchmark
publishes a split scheme, so this project documents that as unknown rather than
inventing a 70/15/15 split or similar.

## 14. Limitations

- No official benchmark task, item, or score exists to validate any of this against —
  every metric above has been exercised only with synthetic data.
- The seven cognitive dimensions, the per-dimension alignment formula, and the
  page-revisit/action-diversity trajectory heuristics are all provisional and may need
  to change once the actual methodology is known.
- `unnecessary_actions` and monotonic regression are intentionally unimplemented rather
  than guessed at.
- Alignment computation currently only handles `NORMALIZED_SCORE`-kind dimensions;
  categorical/distribution comparison is deferred.

## 15. Provisional vs. confirmed summary

| Element | Status |
|---|---|
| Four research conditions (R0-R3) | CONFIRMED FROM PAPER/BRIEF (identifiers only; R1-R3 unimplemented) |
| Baseline anchor ages 7/10/13/16 | CONFIRMED FROM PAPER |
| Skill-guided age bands | CONFIRMED FROM PAPER |
| Seven cognitive dimensions | PROVISIONAL DESIGN |
| Per-dimension alignment formula (1 − \|diff\|) | PROVISIONAL DESIGN |
| Euclidean/cosine alignment distance | PROVISIONAL DESIGN (raw measurement, not chosen as final) |
| Mahalanobis/distributional/learned alignment | FUTURE RESEARCH |
| Capability-alignment tradeoff formulas | PROVISIONAL DESIGN (raw measurements, no composite asserted correct) |
| Failure taxonomy categories | PROVISIONAL DESIGN |
| Dataset splits | CONFIRMED FROM PAPER (absence) — NullSplitProvider is deliberate, not a gap |
| R3 ablation variants | FUTURE RESEARCH |
| Monotonic regression | FUTURE RESEARCH |

## Scientific restriction (brief §25)

No metric here is shaped to favor a guardrail outcome. `alignment_gain` and
`capability_change` are signed raw differences (can be negative), `relative_capability_
retention` can exceed or fall below 1.0, and `MetricComparison` always reports both
sides' full `DescriptiveStats` rather than a single directional summary. Improvement,
no-improvement, degradation, and mixed results are all representable without any
change to this code.
