# Independent Interactive Cognitive-Age Benchmark — Specification

**This is NOT ChildAgentEval.** It contains no WISC-derived content and is not claimed
to be numerically equivalent to any official benchmark score. It exists because
official ChildAgentEval access was not received (Phase 5) — see
`docs/phase0_findings.md` and `docs/author_access_requirements.md`. The reference
paper's four confirmed Qwen3.5-27B baseline values are used only as a **contextual**
comparison point, never as ground truth for this benchmark.

## 1. Design principle

Every task is original content authored for this project. Tasks measure broad,
publicly-described cognitive/interaction categories (working memory, reasoning,
abstraction, language, visual/spatial reasoning, planning, processing behavior,
integrated reasoning) — these are `INDEPENDENT_BENCHMARK_DIMENSIONS`
(`src/childagenteval_research/benchmark/task_schema.py`), a research design choice, not
a claim that they match any official taxonomy.

## 2. Scope (documented reduction from the brief's illustrative 8×3×4=96)

**32 task instances**: 8 categories × 4 anchor ages (7, 10, 13, 16) × **1 task per
cell** (not 3). This reduction was made *before* any pilot spend and is **not**
budget-driven — Qwen3.5-27B's OpenRouter pricing (~$0.0000002/prompt token,
~$0.0000016/completion token) makes even the full 96-instance design trivially cheap in
dollar terms. The actual constraint is *operational reliability within one working
session*: each task requires hand-authored, individually-verified original content
(three arithmetic/logic errors were caught and fixed during authoring — see git history
on `benchmark/tasks/`), and each real task-run involves tens of seconds of real
Chromium+LLM latency per step. 32 instances × 4 conditions (L0-L3) = 128 real task
episodes is the scope judged reliably executable and verifiable in this session; it
preserves **balanced coverage** across all 8 categories and all 4 ages (verified by
`tests/test_benchmark_task_schema.py`).

## 3. Age conditions

Each age gets an *independently authored, difficulty-scaled* task per category (e.g.
`working_memory` sequence length grows 3→4→5→6 items from age 7→16; `planning` step
count and distractor count grow similarly) — age is not communicated to the model via a
bare "you are 7 years old" prompt substitution; it's expressed through task difficulty
design, per the brief.

## 4. Task specification

Every task is a JSON file under `benchmark/tasks/<category>/<task_id>.json`
(`task_schema.TaskDefinition`), with exactly the fields the brief requires:
`task_id, category, target_age, difficulty, instructions, initial_state
(stimulus/choices), available_actions, success_condition, failure_condition,
maximum_steps, scoring_rule, dimension, version`. Two `interaction_kind`s are used
project-wide: `multiple_choice` (click one button among several, then Finish) and
`sequence_click` (click a set of buttons in a specific order, then Finish) — chosen so
scoring is fully mechanical (§8) rather than requiring free-text judgment.

## 5. Answer-leakage prevention

`success_condition`/`failure_condition` (the correct answer/order) are **never**
rendered into the HTML page (`benchmark/task_page.py`) or exposed in any Observation
the agent receives. Scoring (`benchmark/scoring.py`) determines correctness entirely
post-hoc, by comparing the agent's own recorded click targets against
`success_condition` — there is nothing on the page for the agent to read that reveals
correctness.

## 6. Validation

`task_schema.validate_task()` runs deterministic structural checks (§7 of the brief):
valid dimension, valid interaction kind, non-empty instructions, positive
`maximum_steps`, `finish` always available, `multiple_choice`/`sequence_click`-specific
schema checks (choice-id uniqueness, success_condition references an actual
choice/target id), binary-only scoring rule. `load_all_tasks()` additionally rejects
duplicate `task_id`s. "Not copied from WISC/ChildAgentEval" is a human/authoring
guarantee this code cannot verify automatically — every task was hand-written for this
project (see `tests/test_benchmark_task_schema.py` for the full automated checks that
*can* run, and Phase 2.5/5's repository-wide WISC/ChildAgentEval content scans for the
process-level guarantee).

Each task's actual rendered page was also verified end-to-end against a real (non-mocked)
Chromium instance before any model was run against it — this caught a real environment
bug (see `docs/phase5b_independent_benchmark_report.md`, "Environment Fix").

## 7. Scoring

Binary, documented formula (`benchmark/scoring.py`): 1.0 if the agent's final choice
(multiple_choice) or exact click order (sequence_click) matches `success_condition`,
else 0.0. No attempt is made to reproduce the reference paper's proprietary/undisclosed
scoring. Primary task-performance score = unweighted mean of per-task binary scores
(`scoring.mean_task_score`). Category-level scores = mean within each category
(`scoring.category_scores`).

## 8. Cognitive alignment

`benchmark/independent_alignment.py` — an explicitly independent, documented formula
(not a claim of equivalence to the paper's score): a linear target-performance curve
from 0.35 (age 7) to 0.95 (age 16) per dimension, compared against the model's actual
observed per-category scores using the generic profile/alignment machinery from Phase 3
(`evaluation/profiles.py`, `evaluation/alignment.py`; Euclidean distance). Validated
against synthetic data before use (`tests/test_benchmark_independent_alignment.py`):
perfect target match → alignment 1.0; large mismatch → materially lower alignment;
uniform "random-ish" behavior → not artificially high, and further from target at ages
where the target itself is further from 0.5.

## 9. Guardrails (L1/L2/L3)

Real, rule-based, fully logged — no opaque "magic" correction (brief §12):

- **L1-v1** (`guardrails/l1_output.py`): inspects only the model's *raw text output*.
  Allows a clean single-JSON-action response; extracts and uses (MODIFY) a valid action
  JSON found inside a response padded with extra prose; rejects (REJECT) a response with
  no extractable valid action at all. Never sees hidden task state.
- **L2-v1** (`guardrails/l2_action.py`): inspects the *parsed proposed action* against
  the same `Observation.available_elements` the agent itself received. Rejects a
  `finish` issued as the very first action (no attempt made), and rejects any
  click/type/select whose target isn't in the agent's own available-elements list.
- **L3-v1** (`guardrails/l3_dynamic.py`): inspects the episode's own recorded history.
  Substitutes `wait` for an exact repeat of the immediately-preceding action; forces
  `finish` once a task reaches `EXCESSIVE_STEPS_THRESHOLD` (5) steps without completing
  (checked *before* the repeat rule, so a stuck-repeating trajectory can still be
  force-completed rather than looping forever on `wait`→`wait` substitutions — a real
  ordering bug caught and fixed while testing, see phase report).

All three guardrails are unit-tested with synthetic contexts
(`tests/test_guardrails_l1_l2_l3.py`), zero inference cost.

## 10. Fairness across L0-L3

Same model (`qwen/qwen3.5-27b`), same 32 tasks, same temperature (0), same
`max_output_tokens` (128), same `maximum_steps` per task, same scoring, same
`standard_age_prompt` placeholder text, same `Agent`/`run_episode` loop
(`scripts/run_independent_benchmark.py`) — only the guardrail object passed to
`run_episode` changes between conditions. Any further deviation is documented in
`docs/phase5b_independent_benchmark_report.md`.
