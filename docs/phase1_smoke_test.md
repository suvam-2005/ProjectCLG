# Phase 1 — Safe API Smoke Test + Cost Validation

Date: 2026-08-24. One real OpenRouter request was made in this phase. No benchmark,
no Playwright, no loop, no retries.

## Environment

- OS: Windows 11 Home Single Language 10.0.26200
- Python: 3.14.2 (in a project-local `.venv`)
- Key packages: `httpx==0.28.1`, `PyYAML==6.0.3`, `python-dotenv==1.2.3`,
  `pytest==9.1.1`, `pytest-mock==3.15.1`
- Model: `qwen/qwen3.5-27b` (OpenRouter canonical slug `qwen/qwen3.5-27b-20260224`),
  vision-language, 262,144 context tokens — verified live against the OpenRouter
  `/models` endpoint immediately before the call.
- Config: `configs/qwen_baseline.yaml` — `temperature: 0`, `guardrail: none` (L0).
  `scripts/smoke_test_phase1.py` hard-refuses to run if the loaded config's model or
  temperature differ from `qwen/qwen3.5-27b` / `0`.
- `OPENROUTER_API_KEY` is read exclusively from the environment (via a local `.env`,
  loaded with `python-dotenv`). It is never read from any config file, never logged,
  never printed by any script, and confirmed absent from both the cost ledger and the
  trajectory record (see Budget Safety below).

## 1. Local test results (run before the API call)

`pytest -v` — **18/18 passed**, 0 failed, 0 skipped.

| Requirement | Test(s) | Result |
|---|---|---|
| Hard budget limit blocks over-budget requests | `test_rejects_request_that_would_exceed_budget`, `test_record_actual_raises_if_cumulative_exceeds_budget` | PASS |
| Persistent cost ledger survives process restarts | `test_ledger_persists_across_instances` | PASS |
| Requests blocked *before any network call* once budget/call/task caps are hit | `test_budget_guard_blocks_call_before_any_network_request`, `test_rejects_beyond_max_api_calls`, `test_rejects_beyond_max_tasks` | PASS |
| API key never written to the ledger or returned results | `test_api_key_never_written_to_ledger_file`, assertion inside `test_successful_call_records_actual_cost_and_returns_structured_result` | PASS |
| Failed requests do not increase recorded cost | `test_failed_request_does_not_record_cost` (mocked HTTP 500 → `record_actual` never called, cumulative cost stays 0) | PASS |
| Soft budget ($8) warns without blocking; hard budget ($10) still blocks | `test_soft_budget_warns_but_does_not_block`, `test_never_exceeds_budget_over_many_calls` | PASS |
| Config never overrides the approved model/temperature | `test_loads_qwen_baseline_config` | PASS |

Only after all 18 passed did the real API call run.

## 2. API Test

- **Request**: single `chat/completions` call, `qwen/qwen3.5-27b`, `temperature=0`,
  `max_tokens=16`, `response_format: {"type":"json_object"}`, `reasoning: {"enabled": false}`.
  Prompt: `Reply with exactly this JSON and nothing else: {"status": "ok"}`.
- **Response**: `{"status": "ok"}` — exact match, no chain-of-thought, no extra text.
- **request_id**: `gen-1787547019-3zRRjz6SkxbzVxOvm5dN`
- **input_tokens**: 41 (reported `usage.prompt_tokens`, not the pre-request estimate)
- **output_tokens**: 7
- **total_tokens**: 48
- **latency**: 23.46 s (first-call/cold-start latency on OpenRouter; not necessarily
  representative of steady-state)
- **actual cost**: $0.000018915

Full raw record: `runs/phase1_smoke_test/trajectory.json` and `summary.json`. Cost
ledger: `.state/cost_ledger.json` (gitignored local state).

## 3. Cost Projection

**Cost per request (measured, this exact call): $0.000018915**
(pricing used: prompt $0.000000195/token, completion $0.00000156/token, fetched live
from OpenRouter `/models` — not hardcoded)

| Requests | ACTUAL vs PROJECTED | Cost (USD) |
|---:|---|---:|
| 1 | ACTUAL (measured) | $0.000018915 |
| 10 | PROJECTED (linear extrapolation) | $0.00018915 |
| 100 | PROJECTED | $0.0018915 |
| 500 | PROJECTED | $0.0094575 |
| 1,000 | PROJECTED | $0.018915 |
| 5,000 | PROJECTED | $0.094575 |
| 10,000 | PROJECTED | $0.18915 |

**These projections are almost certainly a large underestimate of real benchmark cost,
and should not be used to plan the actual experiment budget.** Reasons:

- This smoke-test prompt (41 input / 7 output tokens) is a trivial text-only ping. The
  paper's DOM-assisted mode sends a **screenshot plus a sanitized accessibility tree**
  on every step — image tokens and structured DOM text are typically one to two orders
  of magnitude larger than 41 tokens per turn.
- **One API request does not equal one benchmark item.** ChildAgentEval is described as
  an interactive, multi-step environment ("inspect state → decide action → execute →
  observe → continue until completion"), so a single item may require several model
  calls (one per step) before scoring. Phase 0 could not determine exact steps-per-item
  or items-per-subtest from public materials, so no reliable request-count estimate
  exists yet for the real benchmark.
- Until either (a) official access clarifies real per-item call/token volume, or (b) we
  scope our own harness tasks and measure their actual multimodal token usage, any
  "cost of the full benchmark" number is a guess dressed up as a calculation. This
  smoke test only proves the pipe works and gives a real per-token price — not a
  meaningful total-experiment forecast.

## 4. Budget Safety

- Hard limit: `MAX_BUDGET_USD=10.00`, enforced in `CostGuard.check_before_request`
  (pre-flight, before any HTTP call) and again in `CostGuard.record_actual` (post-flight,
  raises immediately if actual cumulative spend somehow exceeds the cap).
- Soft limit: `SOFT_BUDGET_USD=8.00`, implemented as a non-blocking `UserWarning` fired
  once when cumulative spend crosses it (`test_soft_budget_warns_but_does_not_block`).
  Not tested against a real spend — validated with mocked/unit-level amounts only, per
  the instruction not to spend money just to test the limit.
- Ledger: `.state/cost_ledger.json`, updated atomically after every completed call,
  reloaded and honored across process restarts.
- After this one real call: **cumulative_cost_usd = $0.000018915**, i.e. 0.00019% of the
  $10.00 hard budget and 0.00024% of the $8.00 soft budget. Neither threshold is close
  to being crossed.

## 5. Reproducibility

- Config used: `configs/qwen_baseline.yaml` (`run_id: qwen_baseline_l0_dev`,
  `model: qwen/qwen3.5-27b`, `temperature: 0`, `guardrail: none`,
  `benchmark_mode: dom_assisted`, `target_age: 10`).
- Script: `scripts/smoke_test_phase1.py` — deterministic given the same prompt, model,
  and `temperature=0` (OpenRouter does not guarantee bit-exact determinism across
  provider routing, only greedy decoding).
- Task ID: `phase1_smoke_test`. Run artifacts: `runs/phase1_smoke_test/`.

## Issues encountered

- Latency (23.46 s) was higher than expected for a 7-token completion; not investigated
  further since this phase only required one successful call, not performance
  characterization.
- The API key was pasted directly into the chat conversation by the user rather than
  placed only in `.env`. It was written to the (gitignored) `.env` file and not
  otherwise logged or reused, but it is present in this conversation's history. The user
  was advised to consider rotating the key on OpenRouter.
- No other issues. All 18 unit/integration tests passed on the first run after the
  soft-budget feature was added.

## Recommendation

The infrastructure (OpenRouter → Qwen3.5-27B → inference client → cost control →
telemetry) is **validated and safe to reuse** for further controlled, small-scale calls.

It is **not** ready — and cannot yet be made ready — for a real benchmark run, because:
1. The actual ChildAgentEval task content, scoring, and DOM environment remain
   unavailable (Phase 0 finding), and
2. Realistic per-item cost cannot be estimated until either official access responds or
   we scope actual multimodal task prompts — the projections above are a floor, not a
   budget plan.

This smoke test validates the plumbing only. It is not a reproduction of ChildAgentEval,
and should not be cited as one.
