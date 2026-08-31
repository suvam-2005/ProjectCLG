# Phase 5C — Pilot Reliability Investigation, Fix, and Full-Benchmark Freeze

Date: 2026-08-24. Real OpenRouter spend this phase: pilot run_02 (~$0.005631). Combined
benchmark ledger after this phase: **$0.015363270** (pilot run_01 + run_02, both
condition L0). Project-wide ledger: **$0.015382185** (Phase 1 smoke test +
pilot run_01 + run_02).

## 1. Malformed-output investigation

All 6 malformed-output events (across 5 of the pilot's 8 tasks: `integrated_age10_v1`
x2, `language_age10_v1`, `planning_age10_v1`, `processing_age10_v1`,
`reasoning_age10_v1`) show the **identical failure signature**:
`error: "expected a JSON object, got int"` — `parse_action()` correctly rejected a
syntactically-valid-JSON response that was a bare scalar (e.g. `"5"`, or a degenerate
250+ character repeated/incrementing-digit string like `"50000...0"` or
`"5678901234...456"`) instead of the required `{"action": ..., "target": ...}` object.

Root-cause classification (brief §1's checklist):

| Candidate cause | Verdict |
|---|---|
| Model formatting | **YES — this is it.** The model emitted a bare JSON scalar. |
| Prompt ambiguity | Partially — the old instructions never explicitly forbade a bare scalar. Fixed (see §3). |
| Action schema | No — the schema itself is correct; it's what correctly rejected the malformed output. |
| Parser | No — `parse_action()` behaved exactly as designed (`json.loads` succeeded, type-check on the result correctly failed). |
| JSON extraction | Not applicable — there was no extra text to extract; the entire response *was* the (wrong-typed) JSON value. |
| Environment adapter | No — unrelated; these are pre-action-execution failures, not environment errors. |
| Timeout | No — no timeouts occurred in either pilot run. |
| Retry/recovery logic | No — recovery worked exactly as designed (see §2). |

Notably, the degenerate long-digit-string responses (250+ characters) appeared
specifically after 2-3 identical prior turns that had already produced the same
click action — this project's L0 prompt is stateless per step (no conversation
history is carried between steps; `prompts.build_l0_messages` rebuilds a fresh
single-turn prompt from the current observation each time), so an unchanged
observation produces a near-identical prompt on consecutive steps. At `temperature=0`
this should be near-deterministic, but OpenRouter explicitly does not guarantee
bit-exact determinism across provider routing — the repeated near-identical context is
the most likely trigger for the occasional degenerate output, though this is an
**observation**, not a confirmed mechanism (INTERPRETATION, not fact).

Original malformed responses are preserved verbatim in
`action.proposed.metadata.raw_model_output` in every affected trajectory record (see
`data/independent_benchmark/pilot/run_01/raw/trajectories/L0/*.jsonl`) — nothing was
discarded or altered.

## 2. Scientific validity of recovery

The recovery policy already met the brief's bar without modification:

- **Malformed output is recorded**: `TrajectoryRecord.error` set to the exact
  validation message.
- **Original model output remains immutable**: preserved verbatim in
  `raw_model_output`, never edited or reinterpreted.
- **Recovery action is separately recorded**: `Action.source = "malformed_recovery"`,
  distinct from `"model"`; `TrajectoryRecord.recovery` set to a fixed description.
- **Recovery count is reported**: `TaskRunResult.recoveries`.
- **Scoring effect is traceable, and in fact provably neutral**: the substituted
  action is always `wait`, which is never a `click` — `scoring.extract_click_targets()`
  only reads `click` actions, so a `wait` can never inject a false answer. This is
  confirmed empirically, not just by code inspection: **run_01 (6 recovery events) and
  run_02 (0 recovery events) produced identical per-task correctness and identical
  per-task step counts** on the same 8 tasks (see §4). If recovery had been biasing
  results, this identity would not hold.

Conclusion: **the recovery behavior was already scientifically acceptable** — it does
not give the model an action it did not produce (a `wait` is not a guess at intent),
and it demonstrably does not change scored outcomes. No change to the recovery
mechanism itself was necessary. This policy applies uniformly to L0-L3 (no guardrail
changes it).

## 3. Fix applied

Per brief §3 ("if legitimate model-output failure, do not artificially suppress it;
improve the schema/prompt only if part of the pre-registered baseline interface and
does not provide task-specific assistance"): `prompts.ACTION_SCHEMA_INSTRUCTIONS` (the
same text sent identically for every task, every age, every condition) was extended to
explicitly forbid bare-scalar responses and give a concrete example:

> "Your entire response must be a single JSON OBJECT starting with '{' and ending with
> '}' — never a bare number, a bare string, or a JSON array. For example, to click an
> element: {"action": "click", "target": "#choice_a"}. Do not respond with just a
> number or letter, even if the on-screen choice is labeled with one — always wrap it
> in the JSON object shown above."

This is a **format-validity fix, not a correctness-directed one**: it was written from
inspecting the *shape* of the failures (a bare scalar) before looking at which tasks
scored correct or incorrect, and it was not tuned per-task or per-category. Two of the
five affected tasks (`integrated_age10_v1`, `language_age10_v1`) still scored
**correct** even before this fix — the malformed events were never the reason a task
failed. Regression tests added: `tests/test_prompts.py`,
`tests/test_actions.py::test_rejects_bare_json_integer` /
`test_rejects_bare_json_string`.

## 4. Pilot re-run comparison (run_01 vs run_02)

Identical 8 tasks (one per category, age 10), identical model/temperature/scoring/
environment/step-limits/task-ordering, condition L0 only, per brief §4.

| | Run_01 (pre-fix) | Run_02 (post-fix) |
|---|---:|---:|
| Malformed-output events | 6 | **0** |
| Recovery events | 6 | **0** |
| Correct / 8 | 4 (50%) | 4 (50%) |
| Per-task steps (in task order) | 4,4,4,6,4,4,4,7 | 4,4,4,6,4,4,4,7 |
| Total steps | 37 | 37 |
| Cost | $0.006588 | $0.005631 |
| Wall-clock | ~15.4 min | ~15.0 min |

Per-task correctness and step counts are **identical** between runs — strong evidence
the harness is reproducible and that the fix eliminated the malformed-output failure
mode without changing anything about how tasks are scored. Cost/latency differ only by
normal run-to-run variance (input token counts differ slightly because the fixed
prompt is marginally longer).

**Notable finding, not previously visible**: every single task in both runs consumed
its full per-task `maximum_steps` budget — the agent never voluntarily finished early.
Full-benchmark cost/time projections (§6) are based on this actually-observed
steps-per-task, not an optimistic minimal-episode assumption.

## 5. Go/no-go criteria (brief §5)

| Criterion | Status |
|---|---|
| A. No infrastructure/parser bug remains | **PASS** — run_02 had zero malformed events |
| B. All recovery behavior explicitly represented in telemetry | **PASS** — was already true; verified in both runs |
| C. Execution policy is reproducible | **PASS** — identical accuracy/steps across two independent runs |
| D. No benchmark task leaks answers | **PASS** — by design (scoring.py never reads task correctness from the rendered page; see `docs/independent_benchmark_specification.md` §5) |
| E. No copyrighted/WISC content | **PASS** — no task content was touched this phase; prior repository-wide scans (Phase 2.5/5) found none, and this phase added no new task or WISC-adjacent content |
| F. Cost guard functioning | **PASS** — see §7 |

## 6. Cost projection for the full 128-task-run

Using run_02's actually-observed rate (the clean, fixed data): $0.00563082 / 37 steps =
**$0.0001522/step**; run_01+run_02 agree that every task consumes its full designed
`maximum_steps`. Total steps across all 32 tasks (one condition), summed from each
task's own `maximum_steps`: **152 steps**. Across all 4 conditions: **608 steps**.

| Scenario | Basis | Projected cost | Projected wall-clock (serial) |
|---|---|---:|---:|
| Expected | run_02's observed $/step x 608 steps | **≈ $0.093** | **≈ 4.1 hours** (608 x ~24.4s/step) |
| Conservative (3x) | accounts for longer L1-L3 trajectories, occasional high-token responses | ≈ $0.278 | ≈ 12.3 hours (if latency also tripled, which is not expected — see note) |
| Worst-case (theoretical ceiling) | every one of 608 calls maxes out at ~750 input + 256 output tokens | ≈ $0.332 | not applicable — token ceiling doesn't imply latency ceiling |

Note: the "conservative" wall-clock multiplier is included for completeness but is not
actually expected — latency is dominated by fixed per-call network/inference overhead
(~22-25s observed consistently regardless of token count), not token count, so 4-5
hours is the realistic serial wall-clock estimate regardless of cost scenario.

**Remaining $8 benchmark budget after this phase: $7.984637.** Even the worst-case
projection ($0.332) uses under 4.2% of the remaining cap. **Budget is not a
constraint on proceeding.**

## 7. Cost guard status

Per-condition ledger sharding implemented
(`benchmark/layered_cost_guard.py` + `scripts/run_independent_benchmark.py::
benchmark_ledger_path()`): each condition (L0/L1/L2/L3) writes to its own
`.state/benchmark_cost_ledger_{condition}.json`, eliminating any shared-file write race
for the benchmark-only tracking. Each condition's *effective* hard/soft limit is
computed at process start as `$8.00 / $6.50 minus what the other three conditions have
already spent combined`, so the **combined** $8 cap is still enforced correctly even
though each condition's raw ledger file only sees its own numbers. The whole-project
ledger (`.state/cost_ledger.json`, tracking the $10 lifetime cap) remains a single
shared file — see §8 for why this specifically is not yet safe for true concurrent
writers.

Verified working this phase: pilot run_02 ran under the effective limit correctly
(no false rejections, no budget breach), and the existing project ledger's
pre-pilot balance ($0.000018915) was preserved and correctly built upon (final:
$0.015382185).

## 8. Parallel execution safety (prepared, not launched)

**Per-condition benchmark ledgers**: safe for concurrent writers — each process only
ever touches its own file.

**Whole-project ledger** (`.state/cost_ledger.json`): **not yet safe for true
concurrent writers.** `CostGuard` loads its ledger into memory once at construction and
mutates that in-memory copy on every `record_actual()` call before writing back — two
processes running concurrently would each hold a stale in-memory copy, and the second
process's write could silently clobber the first's update (a classic lost-update race).
Making this safe would require re-reading the ledger from disk inside a lock on every
single check/write, a real architecture change to a class 235+ existing tests already
depend on — not attempted under this phase's time constraint.

**Practical risk assessment**: given real per-condition spend is a few cents at most,
even a worst-case lost update on the project ledger would misreport the *informational*
project total by a trivially small amount — it could not cause a silent breach of the
$8 benchmark cap (each condition's own effective-limit check, computed from the
per-condition shards, still holds) or the $10 project cap in any practically meaningful
way at these dollar amounts. The risk is real but low-consequence.

**Recommendation**: run the four conditions **serially** (one at a time), per the
brief's own explicit fallback guidance ("if parallel execution is unreliable, fall back
to controlled serial/batched execution... do not trade reproducibility for speed").
Given the trivial dollar amounts involved, a user who prioritizes wall-clock time over
this residual risk could reasonably choose parallel execution instead — that tradeoff
is disclosed here for an explicit decision, not made unilaterally.

## 9. Frozen configuration

`configs/experiments/final_benchmark.yaml` — model, temperature, max tokens,
environment, extra request params, recovery policy, all four conditions'
guardrail versions, budget limits, and the exact git commit and task-set SHA-256
fingerprint this freeze corresponds to. No task, prompt, scoring, or guardrail-logic
change is permitted after this point without creating a new `benchmark_version`.

- **Git commit at freeze**: `849542ba9768e4e1297a735f56bd03ad0c6e84f4`
- **Task set fingerprint**: `4e6ae6752b69bae171fe56f2918ec7c8b773f00d5581824d89747e87afe73df8` (SHA-256 of all 32 task JSON files, concatenated in sorted path order)
- **32 tasks**, 8 categories x 4 ages x 1 task, balanced (verified by
  `tests/test_benchmark_task_schema.py`)
