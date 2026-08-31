# Publication Tables

All values read directly from `data/independent_benchmark/processed/` and
`data/independent_benchmark/statistics/` — nothing hand-typed. Frozen at commit
`849542ba9768e4e1297a735f56bd03ad0c6e84f4`.

## Table 1 — Models and configurations

| model | provider | temperature | max_output_tokens | modality |
|---|---|---:|---:|---|
| qwen/qwen3.5-27b | openrouter | 0 | 256 | text+image+video→text |

## Table 2 — Reference methodology vs our reproduction

See `docs/reproduction_specification.md` for the full component-by-component table.
Summary: official ChildAgentEval access remains unavailable; this run used the
Independent Interactive Cognitive-Age Benchmark instead (`docs/independent_benchmark_specification.md`).

## Table 3 — Reference results (Qwen3.5-27B, paper-reported)

| age | total_composite_score | confidence | status |
|---:|---:|---|---|
| 7 | 0.32 | medium | confirmed (cross-verified) |
| 10 | 0.34 | medium | confirmed (cross-verified) |
| 13 | 0.29 | medium | confirmed (cross-verified) |
| 16 | 0.30 | medium | confirmed (cross-verified) |

Source: `reference/reference_results.json`.

## Table 4 — Our independent-benchmark results (L0-L3)

| condition | n | mean_accuracy | alignment |
|---|---:|---:|---:|
| L0 | 32 | 0.5625 | 0.51875 |
| L1 | 32 | 0.5625 | 0.51875 |
| L2 | 32 | 0.5625 | 0.51875 |
| L3 | 32 | 0.5625 | 0.51875 |

## Table 5 — L0-L3 comparison (paired, same 32 tasks)

| comparison | task_performance_diff | n |
|---|---:|---:|
| L0 vs L1 | 0.000 | 32 |
| L0 vs L2 | 0.000 | 32 |
| L0 vs L3 | 0.000 | 32 |

Intervention/trajectory/token/cost diffs are in Table 8 (L0 vs L3 is the only condition
with any interventions to compare).

## Table 6 — Statistical significance / effect sizes

| comparison | n1 | n2 | welch_t | p_value | cohens_d_paired |
|---|---:|---:|---:|---:|---|
| L0 vs L1 | 32 | 32 | 0.000 | 1.000 | undefined (zero variance in differences) |
| L0 vs L2 | 32 | 32 | 0.000 | 1.000 | undefined (zero variance in differences) |
| L0 vs L3 | 32 | 32 | 0.000 | 1.000 | undefined (zero variance in differences) |

No multiple-comparison correction applied — with all three differences already exactly
zero, correction would not change any conclusion.

## Table 7 — Failure analysis

**Not populated this phase.** Per-step failure-category classification
(`evaluation/failure_taxonomy.py`) was not run against the 128 trajectories; only
aggregate error/recovery counts were computed (Table 8). Flagged as future work.

## Table 8 — Token/cost analysis

| condition | input_tokens | output_tokens | api_calls | cost_usd | errors | recoveries |
|---|---:|---:|---:|---:|---:|---:|
| L0 | 102,911 | 2,162 | 152 | $0.023440 | 2 | 2 |
| L1 | 102,926 | 2,139 | 152 | $0.023407 | 2 | 2 |
| L2 | 102,892 | 2,220 | 152 | $0.023527 | 1 | 1 |
| L3 | 96,260 | 2,058 | 143 | $0.021981 | 2 | 2 |

## Table 9 — Ablation results

**Not populated.** No L3 ablation variants (without-memory-control, without-reasoning-
control, etc.) were run this phase — out of scope for this run.
