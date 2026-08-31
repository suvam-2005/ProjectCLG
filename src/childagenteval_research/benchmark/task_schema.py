"""Task definition schema for the Independent Interactive Cognitive-Age Benchmark.

Every task is loaded from a JSON file under benchmark/tasks/ — no task content is
ever embedded in Python source. The success/failure condition is used only by
scoring.py, applied post-hoc to the agent's recorded action trajectory; it is never
rendered into the page the agent sees, so the page cannot leak the answer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

INDEPENDENT_BENCHMARK_DIMENSIONS: tuple[str, ...] = (
    "working_memory",
    "reasoning",
    "abstraction",
    "language",
    "visual_spatial",
    "planning",
    "processing_behavior",
    "integrated_reasoning",
)

VALID_INTERACTION_KINDS = {"multiple_choice", "sequence_click"}


@dataclass(frozen=True)
class TaskDefinition:
    task_id: str
    category: str
    dimension: str
    target_age: int
    difficulty: str
    version: str
    instructions: str
    interaction_kind: str
    stimulus: dict[str, Any]
    available_actions: tuple[str, ...]
    success_condition: dict[str, Any]
    failure_condition: dict[str, Any]
    maximum_steps: int
    scoring_rule: dict[str, Any]
    time_limit_if_any: float | None = None
    choices: tuple[dict[str, str], ...] = ()

    @classmethod
    def from_json(cls, path: Path) -> "TaskDefinition":
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            task_id=raw["task_id"],
            category=raw["category"],
            dimension=raw["dimension"],
            target_age=raw["target_age"],
            difficulty=raw["difficulty"],
            version=raw["version"],
            instructions=raw["instructions"],
            interaction_kind=raw["interaction_kind"],
            stimulus=raw["stimulus"],
            available_actions=tuple(raw["available_actions"]),
            success_condition=raw["success_condition"],
            failure_condition=raw["failure_condition"],
            maximum_steps=raw["maximum_steps"],
            scoring_rule=raw["scoring_rule"],
            time_limit_if_any=raw.get("time_limit_if_any"),
            choices=tuple(raw.get("choices", [])),
        )


class TaskValidationError(ValueError):
    pass


def validate_task(task: TaskDefinition) -> None:
    """Deterministic, structural validation (brief §7). Cannot verify "not copied from
    WISC/ChildAgentEval" automatically — that is a human/process guarantee documented in
    docs/independent_benchmark_specification.md, not something code can check."""
    if task.dimension not in INDEPENDENT_BENCHMARK_DIMENSIONS:
        raise TaskValidationError(f"{task.task_id}: unknown dimension {task.dimension!r}")
    if task.interaction_kind not in VALID_INTERACTION_KINDS:
        raise TaskValidationError(f"{task.task_id}: unknown interaction_kind {task.interaction_kind!r}")
    if not task.instructions.strip():
        raise TaskValidationError(f"{task.task_id}: empty instructions")
    if task.maximum_steps <= 0:
        raise TaskValidationError(f"{task.task_id}: maximum_steps must be positive")
    if "finish" not in task.available_actions:
        raise TaskValidationError(f"{task.task_id}: available_actions must include 'finish' so the episode can terminate")

    if task.interaction_kind == "multiple_choice":
        if len(task.choices) < 2:
            raise TaskValidationError(f"{task.task_id}: multiple_choice requires >= 2 choices")
        choice_ids = [c["id"] for c in task.choices]
        if len(choice_ids) != len(set(choice_ids)):
            raise TaskValidationError(f"{task.task_id}: duplicate choice ids")
        if task.success_condition.get("type") != "single_choice":
            raise TaskValidationError(f"{task.task_id}: multiple_choice tasks require success_condition.type == 'single_choice'")
        if task.success_condition.get("correct_choice_id") not in choice_ids:
            raise TaskValidationError(f"{task.task_id}: success_condition references a choice id that doesn't exist")

    if task.interaction_kind == "sequence_click":
        if task.success_condition.get("type") != "exact_sequence":
            raise TaskValidationError(f"{task.task_id}: sequence_click tasks require success_condition.type == 'exact_sequence'")
        expected = task.success_condition.get("expected_target_order")
        if not expected or not isinstance(expected, list):
            raise TaskValidationError(f"{task.task_id}: exact_sequence requires a non-empty expected_target_order list")
        targets = {t["id"] for t in task.stimulus.get("targets", [])}
        if not set(expected).issubset(targets):
            raise TaskValidationError(f"{task.task_id}: expected_target_order references a target id not present in stimulus.targets")

    if task.scoring_rule.get("type") != "binary":
        raise TaskValidationError(f"{task.task_id}: only binary scoring_rule is implemented — got {task.scoring_rule.get('type')!r}")


def load_all_tasks(tasks_dir: Path) -> list[TaskDefinition]:
    tasks = [TaskDefinition.from_json(p) for p in sorted(tasks_dir.rglob("*.json"))]
    seen_ids: set[str] = set()
    for task in tasks:
        if task.task_id in seen_ids:
            raise TaskValidationError(f"duplicate task_id: {task.task_id}")
        seen_ids.add(task.task_id)
        validate_task(task)
    return tasks
