"""Trajectory record schema for every logged interaction step. No API secrets are
ever written into these records."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TrajectoryRecord:
    experiment_id: str
    run_id: str
    task_id: str
    subtest: str
    target_age: int
    model: str
    provider: str
    condition: str  # e.g. "L0_none", "L1_output", "L2_action", "L3_dynamic"
    timestamp: float
    step_number: int
    observation_metadata: dict[str, Any]
    action: dict[str, Any]
    action_result: dict[str, Any]
    latency_s: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    cumulative_cost_usd: float
    error: str | None = None
    recovery: str | None = None
    final_score: float | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()
