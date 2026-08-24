# ChildAgentEval Research — Reproduction & Guardrail Study

Reproducing the Qwen3.5-27B baseline from *Evaluating Cognitive Age Alignment in
Interactive AI Agents* (arXiv:2605.17894 / ChildAgentEval, PediaMedAI), then studying
whether external cognitive guardrails (L1 output, L2 action, L3 dynamic trajectory-level)
improve cognitive-age alignment relative to an L0 no-guardrail control.

**Status: Phase 0-2 complete.** Start with
[`docs/phase0_findings.md`](docs/phase0_findings.md), then
[`docs/phase1_smoke_test.md`](docs/phase1_smoke_test.md), then
[`docs/phase2_l0_infrastructure.md`](docs/phase2_l0_infrastructure.md).

Phase 0's critical finding: the official ChildAgentEval repository contains no benchmark
code, task definitions, scoring rubrics, or data — only a paper summary and an
access-request process (evaluation is administered by the authors on request, since the
items derive from copyrighted Wechsler Intelligence Scale for Children materials). This
materially changes what "reproduction" can mean here; read the findings doc for the full
breakdown and the two-track plan proposed in response.

## Layout

- `docs/phase0_findings.md` — repository/paper inspection report (this is the source of
  truth for what is and isn't publicly available).
- `configs/` — YAML experiment configs. Never edit parameters in source; edit here.
- `src/childagenteval_research/cost_guard.py` — hard budget/call/task/token guard, backed
  by a local JSON ledger (`.state/cost_ledger.json`, gitignored).
- `src/childagenteval_research/guardrails/interface.py` — the `GuardrailResult` /
  `Guardrail` protocol shared by L0-L3. Only `NoGuardrail` (L0) exists so far.
- `src/childagenteval_research/telemetry/schema.py` — `TrajectoryRecord`, the per-step log schema.
- `src/childagenteval_research/agent.py` — the `Agent` controller and `run_episode()`,
  the only place Agent + Guardrail + Environment are wired together.
- `src/childagenteval_research/actions.py` — the generic structured-action schema and
  the fixed malformed-output recovery action.
- `src/childagenteval_research/environment/` — `base.py` (the `Environment` protocol +
  `OfficialBenchmarkUnavailableError`), `mock_environment.py` (NOT ChildAgentEval —
  harness testing only), `playwright_adapter.py` (generic, no benchmark selectors),
  `factory.py` (the single switch point for plugging in the real benchmark later).
- `src/childagenteval_research/reproduction_kind.py` — enforces the
  `OFFICIAL_REPRODUCTION` (blocked) vs `INDEPENDENT_EXPERIMENT` distinction.
- `src/childagenteval_research/experiment_identity.py` — `experiment_id`, `run_id`,
  `git_commit`, `configuration_hash` for every run.
- `.env.example` — copy to `.env` and set `OPENROUTER_API_KEY`. Never commit `.env`.

## Rules carried over from the brief

- `qwen/qwen3.5-27b` via OpenRouter only, temperature 0, until explicitly told otherwise.
- Hard budget cap: $10.00 total. The cost guard must approve every request before it is
  sent, and halts immediately if actual cumulative spend ever exceeds the cap.
- L0 must be validated as a clean control before L1 is implemented, L1 before L2, etc.
- Keep dev/validation/test splits separate; never tune guardrail thresholds on test.
- No benchmark item, task, or score is ever invented — anything not publicly available is
  documented as unavailable, not reconstructed from assumption.
