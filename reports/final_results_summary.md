# Final Results Summary

Independent Interactive Cognitive-Age Benchmark (NOT ChildAgentEval), Qwen3.5-27B,
frozen at git `849542ba9768e4e1297a735f56bd03ad0c6e84f4`. Full detail:
`reports/benchmark_report.md`.

## Reference results (contextual only, not equivalent metrics)

| Age | Reference total composite score |
|---:|---:|
| 7 | 0.32 |
| 10 | 0.34 |
| 13 | 0.29 |
| 16 | 0.30 |

## L0 (no guardrail)

18/32 correct (56.25%). Alignment 0.51875. 152 steps, 105,073 tokens, $0.023440.

## L1 (output guardrail)

18/32 correct (56.25%, identical to L0). Alignment 0.51875 (identical). 0
interventions. 152 steps, 105,065 tokens, $0.023407.

## L2 (action guardrail)

18/32 correct (56.25%, identical to L0). Alignment 0.51875 (identical). 0
interventions. 152 steps, 105,112 tokens, $0.023527.

## L3 (dynamic guardrail)

18/32 correct (56.25%, identical to L0). Alignment 0.51875 (identical). **70
interventions** (48.95% of 143 steps). 143 steps (−5.9%), 98,318 tokens (−6.4%),
$0.021981 (−6.2%).

## Alignment changes

None. All four conditions: 0.51875, exactly.

## Capability changes

None. All four conditions: 0.5625 (18/32), exactly.

## Intervention rates

L0: 0.0%. L1: 0.0%. L2: 0.0%. L3: 48.95%.

## Cost

Combined benchmark spend: **$0.110330** of the $8.00 cap (1.4% used, $7.889670
remaining). Total project spend: **$0.110349** (704 API calls total across the whole
project, including Phase 1's smoke test and both pilots).

## Statistical evidence

Paired comparison, n=32 tasks: L0 vs L1/L2/L3 mean difference = 0.000 in all three
cases (p=1.000; every per-task outcome identical). No effect detected on capability or
alignment for any guardrail. L3's efficiency effect (fewer steps/tokens/cost) is a
direct count from real telemetry, not a statistical inference.

## Limitations

Single run per condition (temperature 0, no repeats); 32-task benchmark (n=4 per
category, n=8 per age) limits power; L1/L2 recorded zero interventions in this run, so
their true effect (if any) remains untested rather than disproven; this benchmark is
original and not validated against any official cognitive-age instrument. Full list:
`reports/benchmark_report.md` §24-25.
