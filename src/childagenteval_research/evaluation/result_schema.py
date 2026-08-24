"""The unified per-task evaluation result schema. Every field the official benchmark
cannot yet supply defaults to None — nothing here requires data we don't have.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .conditions import ResearchCondition
from .profiles import ObservedProfile, TargetProfile


@dataclass
class EvaluationResult:
    experiment_id: str
    run_id: str
    condition: ResearchCondition
    model: str
    provider: str
    task_id: str
    target_age: int | None = None
    subtest: str | None = None

    task_score: float | None = None
    completion: bool | None = None

    target_profile: TargetProfile | None = None
    observed_profile: ObservedProfile | None = None
    alignment_score: float | None = None
    alignment_distance: float | None = None

    intervention_count: int | None = None
    intervention_rate: float | None = None

    trajectory_length: int | None = None
    errors: int | None = None
    recoveries: int | None = None

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    api_calls: int | None = None
    cost_usd: float | None = None

    latency_s: float | None = None

    benchmark_version: str | None = None
    git_commit: str | None = None
    configuration_hash: str | None = None
    timestamp: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return _convert(dataclasses.asdict(self))


def _convert(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _convert(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert(v) for v in obj]
    return obj
