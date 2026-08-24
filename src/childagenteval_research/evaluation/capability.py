"""Task performance container. Every field must be populated from what the official
benchmark adapter actually reports — this module computes nothing and invents no
scoring formula. All fields are nullable because the adapter may not supply all of them.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaskPerformanceResult:
    task_id: str
    subtest: str | None = None
    raw_score: float | None = None
    subtest_score: float | None = None
    completion: bool | None = None
    correctness: float | None = None
    failure: bool | None = None
    reversal_discontinued: bool | None = None
    source: str = "benchmark_adapter"

    def has_any_score(self) -> bool:
        return any(v is not None for v in (self.raw_score, self.subtest_score, self.correctness))
