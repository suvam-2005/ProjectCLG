# Phase 2 — L0 Agent Infrastructure

Date: 2026-08-24. No new real OpenRouter spend in this phase (see §10). The official
ChildAgentEval benchmark remains unavailable pending author access.

## 1. Architecture

```
TaskSpec
   |
   v
Agent.initialize(task) --> Environment.reset(task) --> Observation
   |
   v
Agent.observe(observation)              # L0: pass-through hook only
   |
   v
Agent.decide(observation)               # builds prompt, calls Qwen3.5-27B, parses
   |                                     # the raw text into an Action (or a fixed
   |                                     # recovery Action if parsing fails)
   v
Guardrail.evaluate(context)             # NoGuardrail for L0: always ALLOW
   |
   v
apply_guardrail(proposed, result)       # ALLOW/REJECT/MODIFY -> final Action
   |
   v
Agent.execute(final_action, environment) --> Environment.execute_action -> ActionResult
   |
   v
Agent.record(...)                       # builds + writes a TrajectoryRecord (JSONL)
   |
   v
   ... loop until "finish", environment reports done, or max_steps ...
   |
   v
Agent.terminate() ; Environment.close()
```

`run_episode()` in `src/childagenteval_research/agent.py` is the only place that wires
Agent + Guardrail + Environment together. Agent never imports or references a guardrail
directly — this is what lets L1/L2/L3 be added later (Phase 3+) without touching
`Agent`, matching the "Agent → Guardrail → Action" requirement.

## 2. Agent controller

`src/childagenteval_research/agent.py` — `Agent` class implements exactly the six
requested methods: `initialize`, `observe`, `decide`, `execute`, `record`, `terminate`.

- `observe()` and `terminate()` are intentionally no-op passthroughs for L0 — they exist
  so a future guardrail/preprocessing layer has a documented attachment point.
- `decide()` builds messages via a pluggable `prompt_builder`, calls the model client,
  and parses the response through the action schema (§4). On a validation failure it
  applies the fixed recovery action and does **not** re-query the model.
- `record()` builds a `TrajectoryRecord` (§7) and writes it via `TrajectoryWriter`
  immediately — one JSONL line per step, not buffered per episode.

## 3. Action schema

`src/childagenteval_research/actions.py`. Generic action types only —
`click, type, select, scroll, keypress, wait, finish` — with per-type required fields
(e.g. `type` requires `target` and `text`). `parse_action()` validates a model's raw
text strictly: invalid JSON, non-object JSON, unknown action types, and missing
required fields all raise `ActionValidationError` and never guess at intent.

Recovery: `make_recovery_action()` always returns the same shape — a `wait` action
tagged `ActionSource.MALFORMED_RECOVERY` with the failure reason and the original raw
model text preserved in `metadata`. This is used both for malformed model output and
for a guardrail `REJECT` decision (§ agent.py `apply_guardrail`) — the model's original
proposal is never silently rewritten into something that looks like its own choice.
No automatic retries are issued in either case.

## 4. Playwright adapter

`src/childagenteval_research/environment/playwright_adapter.py`. Generic dispatch for
all seven action kinds via Playwright's sync API (`click`, `fill`, `select_option`,
`mouse.wheel`, `keyboard.press`, `wait_for_timeout`, no-op for `finish`). No
ChildAgentEval selectors or URLs are hard-coded — `reset()` requires the caller to
supply `task.metadata["start_url"]`, and raises `ValueError` if it's missing rather than
defaulting to any guessed URL. Screenshots are optional (`screenshots_dir`); the
accessibility tree is captured via `page.accessibility.snapshot()` when
`dom_assisted=True`, matching the paper's described DOM-assisted mode. `playwright` is
imported lazily and guarded — importing this module doesn't require browser binaries to
be installed, and instantiating it without them raises a clear `RuntimeError`.

This is the documented plug-in point for the real benchmark (see §9).

## 5. Observation representation

`src/childagenteval_research/observation.py` — `screenshot_ref`, `accessibility_tree`,
`page_metadata`, `available_elements`, `task_state`, `done`. The generic Playwright
adapter always sets `task_state=None` and `available_elements=[]` — it never invents
benchmark-specific state. Populating those meaningfully is left to whatever adapter
plugs in the real benchmark, which is expected to enforce the same constraint stated in
`environment/base.py`: no answer keys, scoring info, hidden backend state, or
future-task content may ever appear in an Observation.

## 6. Telemetry

`src/childagenteval_research/telemetry/schema.py` — `TrajectoryRecord` now carries every
field Phase 2 asked for: `run_id, task_id, subtest, target_age, model, provider,
condition, step_number, observation_metadata, action, action_result, latency_s,
input_tokens, output_tokens, cost_usd, cumulative_cost_usd, error, recovery,
final_score`. ("Estimated cost" in the brief is implemented as `cost_usd` — the actual
measured per-step cost from OpenRouter's reported `usage`, which is more precise than a
pre-flight estimate and consistent with how Phase 1 tracked cost.)

`telemetry/writer.py` — `TrajectoryWriter` appends one JSON line per step to a `.jsonl`
file (`Agent.record()` calls this after every step), so a run survives a mid-episode
interruption with a readable partial trajectory.

## 7. Cost controls

`cost_guard.py` is unchanged in its core mechanics (pre-flight check, ledger
persistence, hard stop) but gained the approval gate the brief asked for:

- **Hard budget ($10.00)**: unchanged — blocks before any network call, and again after
  recording actual cost, exactly as validated in Phase 1.
- **Soft budget ($8.00)**: now stronger than Phase 1. Crossing it still fires a
  `UserWarning` once, but every subsequent `check_before_request()` call now raises
  `SoftBudgetApprovalRequiredError` until a human calls
  `CostGuard.approve_continued_spending(reason=...)` — an explicit, non-automatable
  gate. Nothing in this codebase calls that method automatically.
- **Ledger preserved across phases**: the real ledger at `.state/cost_ledger.json` still
  shows Phase 1's `cumulative_cost_usd = 0.000018915` after this phase's test run — no
  test touches it (all cost-guard/agent tests use `tmp_path` ledgers).

## 8. Mock environment

`src/childagenteval_research/environment/mock_environment.py` — `MockEnvironment`,
explicitly named and documented as NOT ChildAgentEval. Supports exactly three trivial
interactions (click a button, type text, finish) solely to exercise the
observe→decide→execute→observe loop. It is never used as, or reported alongside,
benchmark results — the `reproduction_kind.py` module (§14) tags anything produced
through it as `INDEPENDENT_EXPERIMENT`.

## 9. Official benchmark integration point

`src/childagenteval_research/environment/factory.py` is the single switch:

```python
get_environment("official_childagenteval")  # -> raises OfficialBenchmarkUnavailableError
get_environment("mock")                     # -> MockEnvironment()
get_environment("playwright_generic")       # -> PlaywrightEnvironmentAdapter(...)
```

To plug in the real benchmark once access is granted: implement an environment class
satisfying the `Environment` protocol in `environment/base.py`
(`reset(task) -> Observation`, `execute_action(action) -> ActionResult`, `close()`),
using whatever the official benchmark's actual interface and task content turn out to
be, and register it under the `"official_childagenteval"` key in `factory.py`. No other
file (`agent.py`, `actions.py`, telemetry, cost guard) needs to change — that's the
entire point of the abstraction.

## 10. Test results

`pytest -v` — **61/61 passed**, all using mocked inference (`FakeModelClient` in
`tests/test_agent.py`) or a mocked `sync_playwright` (`tests/test_environment.py`); zero
new real OpenRouter calls this phase.

| Area | File | Covers |
|---|---|---|
| Actions | `test_actions.py` | valid parse (click/type/finish), malformed JSON, non-object JSON, unknown type, missing required field, unknown-field passthrough, fixed recovery shape |
| Agent | `test_agent.py` | valid decide, malformed→recovery without re-querying, guardrail ALLOW/REJECT/MODIFY wiring, full episode (click→type→finish) with trajectory persisted, zero-intervention check for L0, max_steps bound when the agent never finishes |
| Environment | `test_environment.py` | MockEnvironment lifecycle (reset/click/type/finish/unsupported-action/closed), factory routing incl. the blocked official adapter, Playwright adapter dispatch/finish/error-handling/close/missing-start_url/playwright-not-installed |
| Telemetry | `test_telemetry.py`, `test_telemetry_writer.py` | record round-trip, no secrets in record, JSONL append/read, parent-dir creation, missing-file read |
| Cost | `test_cost_guard.py` (extended) | hard budget block, ledger persistence, soft-budget warning, soft-budget **approval gate** (new), never-exceeds-budget stress test |
| Reproducibility | `test_experiment_identity.py`, `test_config.py` | unique experiment IDs, config-hash sensitivity, git-commit capture (handles zero-commit repos), L0 config loading, **L0 config rejects any non-`none` guardrail** |

I judged an additional real API call was **not** necessary this phase: Phase 1 already
validated the OpenRouter client end-to-end (auth, model availability, request format,
token/cost accounting) against the real API, and every new Phase 2 behavior (action
parsing, recovery, guardrail wiring, episode control flow) is model-client-agnostic —
mocked inference exercises it completely and more precisely than a real call would
(canned malformed output is otherwise unreliable to elicit on demand). No additional
spend occurred.

## 11. Remaining blockers

- **`OFFICIAL_REPRODUCTION` = BLOCKED.** Unchanged from Phase 0/1: the official
  ChildAgentEval benchmark's task content, scoring, and environment implementation are
  not public. Nothing in this phase changes that; the author access request sent
  earlier is still pending.
- Real per-item token/step cost still cannot be estimated (same caveat as Phase 1's
  report) until either official access responds or real task content is scoped.
- The Playwright adapter has not been run against a real browser (Chromium binaries
  aren't installed and no task has a real `start_url` yet) — only its dispatch logic is
  unit-tested against a mocked `sync_playwright`. This should be exercised once there's
  an actual target (official or otherwise) to point it at.
  **Resolved in Phase 2.5** — see `docs/phase2_5_browser_smoke_test.md`.
