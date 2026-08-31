"""Per-task-run result schema (brief §17). One row per (condition, task) completion,
aggregated from that task's step-level TrajectoryRecords plus its scoring.TaskScoreResult.
Alignment is deliberately None here — alignment is only meaningful aggregated across a
whole age+condition's category scores (see independent_alignment.py); recording it per
task would imply a granularity this metric doesn't have.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TaskRunResult:
    experiment_id: str
    run_id: str
    condition: str
    task_id: str
    category: str
    target_age: int
    model: str
    provider: str
    temperature: float
    guardrail_version: str | None
    steps: int
    correct: bool
    score: float
    outcome: str
    interventions: int
    errors: int
    recoveries: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    latency_s: float
    timestamp: float
    git_commit: str
    configuration_hash: str
    alignment: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def append_task_run_result(result: TaskRunResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result.to_dict()) + "\n")


def read_task_run_results(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
