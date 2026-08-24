"""Dev/validation/test split assignment. The official benchmark has not confirmed
whether it provides splits at all (see docs/phase0_findings.md) — NullSplitProvider is
the current honest default: every task is UNKNOWN until an adapter says otherwise.
Guardrail thresholds must never be tuned against a task tagged TEST.
"""
from __future__ import annotations

from enum import Enum
from typing import Protocol


class DatasetSplit(str, Enum):
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    TEST = "test"


class SplitProvider(Protocol):
    def get_task_split(self, task_id: str) -> DatasetSplit | None: ...


class NullSplitProvider:
    """Always returns None. Use this until an official-benchmark adapter can answer
    the question for real — never invent a split assignment."""

    def get_task_split(self, task_id: str) -> DatasetSplit | None:
        return None
