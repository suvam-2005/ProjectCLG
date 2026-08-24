# Phase 2.5 — Real Chromium Smoke Test + Repository Hygiene

Date: 2026-08-24. Zero OpenRouter calls this phase — verified below.

## Environment

- OS: Windows 11 Home Single Language 10.0.26200
- Python: 3.14.2 (project `.venv`)
- Playwright (Python package): 1.62.0
- Chromium (installed via `playwright install chromium`): 151.0.7922.34
  (revision `chromium-1234`; stale `chromium-1223`, `firefox-1522`, and `webkit-2287`
  caches were removed by the installer — only Chromium was requested, no other browser
  engine was installed)

Note: Playwright's legacy `page.accessibility.snapshot()` API no longer exists in
1.62.0 — it was removed upstream in favor of ARIA snapshots. The generic adapter
(`environment/playwright_adapter.py`) was updated to use
`page.locator("body").aria_snapshot()`, which returns a YAML-like string tree instead of
a dict; `Observation.accessibility_tree` was widened to accept either shape. This is a
library-API fix, not a benchmark-content change.

## Test

`fixtures/local_playwright_smoke_test/index.html` — **LOCAL_PLAYWRIGHT_SMOKE_TEST**, an
original, static, entirely self-authored page (button, text input, select, a "Finish"
button, and a `#status` completion indicator). Explicitly labeled in its own HTML
comment as not ChildAgentEval and not WISC-derived. Real (headless) Chromium results,
via `tests/test_playwright_real_browser.py` (7 tests, all passing against a real
browser, not mocked):

| Check | Result |
|---|---|
| Browser launch | PASS — real Chromium 151.0.7922.34 launched headless |
| Page load | PASS — `page_metadata["url"]` matches the fixture's `file://` URL |
| Screenshot capture | PASS — a non-empty `.png` written to `screenshots_dir` |
| DOM/accessibility observation | PASS — `page.locator("body").aria_snapshot()` returns a real ARIA tree string containing the button/textbox roles |
| Click | PASS — clicking `#start_button` sets `data-state="started"` on the real page |
| Typing | PASS — `#answer_input` reflects the typed value via `input_value()` |
| Select | PASS — `#choice_select` reflects the chosen `value` via `eval_on_selector` |
| Finish (page-level) | PASS — clicking `#finish_button` flips `#status` text to `"completed"` on the real DOM |
| Finish (episode-level) | PASS — the adapter's `finish` action marks `Observation.done = True` without touching the page |
| Clean close | PASS — `close()` was made idempotent (page/browser/playwright refs cleared after closing) so it's safe whether or not a test already closed it |

## L0 Loop

`tests/test_l0_real_browser_loop.py` — the full loop against real Chromium:

```
Observation -> ZeroCostFakeModelClient -> Action -> NoGuardrail -> real Chromium -> new Observation -> ... -> finish
```

5 steps (click start → type answer → select choice → click page-finish → agent finish),
driving the actual `PlaywrightEnvironmentAdapter` against the fixture page —
**PASSED**. `ZeroCostFakeModelClient` never imports or references
`childagenteval_research.openrouter_client`; it cannot make a network call by
construction, not just by not being invoked.

## Telemetry

All 5 steps' `TrajectoryRecord`s (asserted directly from the written JSONL, not just
in-memory) contain every field Part B asked for: `experiment_id, run_id, task_id,
subtest, target_age, model, provider, condition, step_number, observation_metadata,
action, action_result, timestamp, latency_s, input_tokens, output_tokens, cost_usd,
cumulative_cost_usd, error, recovery, final_score`. `model` is recorded as
`"none/fake-model-no-inference"` and `provider` as `"none"` — not `"qwen/qwen3.5-27b"` /
`"openrouter"` — so this run's telemetry can never be mistaken for a real inference
result. Per-step, verified directly: `input_tokens == 0`, `output_tokens == 0`,
`cost_usd == 0.0`, `cumulative_cost_usd == 0.0` for all 5 records. Nothing was
fabricated — these are the real values `ZeroCostFakeModelClient` returns because it
never calls a model.

## Cost

- **OpenRouter inference calls made: 0**
- **Additional OpenRouter spend: $0.00**
- **Total cumulative OpenRouter spend remains: $0.000018915**

Verified directly by re-reading `.state/cost_ledger.json` before and after this phase's
work: `cumulative_cost_usd` is unchanged at `1.8915e-05`, `api_calls_made` is still `1`,
and `tasks_completed` still contains only `"phase1_smoke_test"`. No test or script this
phase constructs a real `CostGuard`/`OpenRouterClient` against that ledger.

## Repository Security

**Secret scan** (pattern search across the working tree, excluding `.venv`/`.git`/
`*.egg-info`, for OpenRouter-key, generic API-key/token/password/private-key patterns):
zero real secrets found. Two benign matches reviewed and confirmed safe:
- `tests/test_openrouter_client.py:92` — a deliberately fake literal
  (`"sk-super-secret-token-12345"`) used only to prove the real key is never written to
  the ledger.
- `src/childagenteval_research/openrouter_client.py:33` — reads
  `os.environ.get("OPENROUTER_API_KEY")`; no value is hard-coded.

The real key (`sk-or-v1-...`) was confirmed present in exactly one file — the
gitignored `.env` — and in zero other files in the working tree (source, tests, YAML,
JSON, docs, `runs/`, `.state/`).

**`.gitignore`**: reviewed, not replaced. Added the entries Part E required that were
missing (`.env.*` with a `!.env.example` exception so the template stays tracked,
`venv/`, `results/`, `trajectories/`, `logs/`, `*.log`) alongside what was already
correct (`.env`, `.state/`, `__pycache__/`, `*.pyc`, `.venv/`). Also added `*.egg-info/`
and `.pytest_cache/`, both leftover local build/test artifacts from `pip install -e .`
and `pytest`, neither of which belongs in version control.

**Benchmark/copyright check** (Part G): searched the full working tree for
Wechsler/WISC/subtest-name references. Every match is either Phase 0's documentation of
what the paper *says* exists (`docs/phase0_findings.md`, `README.md`) or an explicit
disclaimer that a local fixture is *not* derived from it
(`fixtures/local_playwright_smoke_test/index.html`,
`tests/test_playwright_real_browser.py`). No actual item content, images, word lists,
matrices, or scoring rubrics exist anywhere in the repository. Searched separately for
every occurrence of "ChildAgentEval" (17 files) — all are the project's own package
name, disclaimers, or the blocked-adapter logic; none label independently-generated
content as if it were the official benchmark.

## Result

The real Playwright execution layer is validated end-to-end against a real, non-benchmark
page: browser lifecycle, screenshot capture, ARIA-based DOM observation, and all
supported action types (click/type/select/finish) all work against actual Chromium, and
the full Agent → Guardrail → Environment loop drives it correctly with zero inference
cost. It is ready to be pointed at real task content once the official adapter exists;
the ARIA-snapshot API fix means the previous mocked tests' assumptions about the
accessibility API were wrong and are now corrected everywhere (mocked and real).
