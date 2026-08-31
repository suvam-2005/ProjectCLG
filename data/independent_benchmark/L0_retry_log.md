# L0 retry log

**Event**: the full L0 background run (task `byyoidp6v`) was externally terminated
(`status: killed`, no Python traceback in its own output — not a script crash) after
completing 30 of 32 tasks cleanly. `wm_age16_v1` was mid-episode (5 of up to 9 steps
recorded, real API calls already charged and recorded in the ledger) when killed;
`wm_age7_v1` had not yet started.

**Cause**: external process termination, not a bug in the frozen benchmark logic —
all 30 completed tasks have clean, well-formed, internally-consistent results, and the
cost ledger's per-step history for the interrupted task is intact and legible. Not an
infrastructure-corruption or benchmark-integrity stop condition.

**Retry policy applied** (predefined here, before acting):
1. Never resume a partial episode mid-way — no checkpointing exists for that, and
   scoring a partial trajectory as if it were complete would be invalid.
2. The partial trajectory for the interrupted task is preserved, never deleted or
   silently overwritten: moved to `wm_age16_v1.INTERRUPTED_ATTEMPT1_partial.jsonl` in
   the same trajectories directory (5 steps recorded before termination).
3. The interrupted task is re-run **from scratch** as a fresh, complete episode, using
   the identical frozen configuration (same runner script, same config file, same
   guardrail, same model/temperature/steps/scoring — nothing in the frozen benchmark
   was touched).
4. The never-started task is run normally.
5. Both results are appended to the same `data/independent_benchmark/raw/L0.jsonl`
   (append-only; the 30 existing valid rows are untouched).
6. This retry is recorded here, in the results themselves (task_id is identical, so the
   log + timestamp + git_commit/configuration_hash on the row make it traceable), and
   in the final report's "deviations" section.

Cost impact: the partial `wm_age16_v1` attempt's real spend (5 steps, ~$0.0007) is
preserved in the ledger's permanent history and is NOT double-counted or removed — it
is simply additional real spend from a real (if incomplete) attempt, same as any other
recorded API call.

## L1 retry event

During L1 batch 2/8 (integrated_reasoning), `integrated_age7_v1` failed twice in a row
with `httpx.ConnectError: [WinError 10054] An existing connection was forcibly closed
by the remote host` — a network-layer failure raised before any HTTP response was
received, so `CostGuard.record_actual()` was never reached (confirmed no cost charged
for either failed attempt; verified against `tests/test_openrouter_client.py::
test_failed_request_does_not_record_cost`, the same guarantee this behavior already
had test coverage for). No partial trajectory or task result was written for either
failed attempt (the failure occurs before `Agent.record()` is ever called), so nothing
needed to be preserved/renamed this time — unlike the L0 kill, there was no partial
state to reconcile.

Retry policy applied: retried the single missing task via `--task-ids
integrated_age7_v1`, isolated from the rest of the batch (not a blanket re-run of the
whole condition). Succeeded on the 3rd attempt. Two consecutive failures on the same
task before succeeding is noted as a real observation (not explained further —
INTERPRETATION would require more evidence than two data points), not treated as a
benchmark-integrity issue since the failures were entirely at the network-transport
layer, never inside the frozen benchmark logic itself.

## L2 retry event

Same external-kill pattern as the original L0 event: the L2 working_memory batch
(background task `bwf7rojm9`) was killed after completing 2/4 tasks
(`wm_age10_v1`, `wm_age13_v1`). `wm_age16_v1` was mid-episode (8 of up to 9 steps
recorded) when killed; `wm_age7_v1` had not started. Same policy applied: partial
trajectory preserved as `wm_age16_v1.INTERRUPTED_ATTEMPT1_partial.jsonl`, both
remaining tasks re-run as fresh, complete episodes, appended to the same
`data/independent_benchmark/raw/L2.jsonl`.
