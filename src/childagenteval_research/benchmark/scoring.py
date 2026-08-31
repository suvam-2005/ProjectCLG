"""Deterministic, original scoring for the Independent Interactive Cognitive-Age
Benchmark. Scoring never touches the rendered page — it only compares the agent's own
recorded click targets (from its trajectory) against `success_condition`, so nothing
about correctness is ever exposed to the model during the episode.

Formula (documented, not proprietary): each task's raw score is binary — 1.0 if the
agent's final choice (multiple_choice) or exact click order (sequence_click) matches
`success_condition`, else 0.0. The benchmark's primary task-performance score is the
unweighted arithmetic mean of these binary scores across tasks. No other normalization
is applied.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .task_schema import TaskDefinition


class TaskOutcome(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    INVALID_ACTION = "invalid_action"


@dataclass(frozen=True)
class TaskScoreResult:
    task_id: str
    outcome: TaskOutcome
    correct: bool
    score: float
    click_targets_in_order: tuple[str, ...]


def score_task(task: TaskDefinition, click_targets_in_order: list[str]) -> TaskScoreResult:
    if not click_targets_in_order:
        return TaskScoreResult(
            task_id=task.task_id, outcome=TaskOutcome.INVALID_ACTION, correct=False,
            score=task.scoring_rule["incorrect"], click_targets_in_order=(),
        )

    if task.interaction_kind == "multiple_choice":
        selected = click_targets_in_order[-1]
        correct = selected == task.success_condition["correct_choice_id"]
    elif task.interaction_kind == "sequence_click":
        correct = list(click_targets_in_order) == task.success_condition["expected_target_order"]
    else:
        raise ValueError(f"unsupported interaction_kind for scoring: {task.interaction_kind!r}")

    outcome = TaskOutcome.CORRECT if correct else TaskOutcome.INCORRECT
    score = task.scoring_rule["correct"] if correct else task.scoring_rule["incorrect"]
    return TaskScoreResult(
        task_id=task.task_id, outcome=outcome, correct=correct, score=score,
        click_targets_in_order=tuple(click_targets_in_order),
    )


def extract_click_targets(trajectory_records: list[dict]) -> list[str]:
    """Pulls the ordered list of 'click' targets from a task's trajectory (the final,
    post-guardrail action of each step) — the only information scoring is allowed to use."""
    targets = []
    for record in trajectory_records:
        final = record.get("action", {}).get("final", {})
        if final.get("action") == "click" and final.get("target"):
            targets.append(final["target"])
    return targets


def mean_task_score(results: list[TaskScoreResult]) -> float | None:
    if not results:
        return None
    return sum(r.score for r in results) / len(results)


def category_scores(results: list[TaskScoreResult], task_by_id: dict[str, TaskDefinition]) -> dict[str, float | None]:
    by_category: dict[str, list[TaskScoreResult]] = {}
    for r in results:
        category = task_by_id[r.task_id].category
        by_category.setdefault(category, []).append(r)
    return {category: mean_task_score(rs) for category, rs in by_category.items()}
