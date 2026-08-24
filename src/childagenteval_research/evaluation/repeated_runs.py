"""Repeated-run bookkeeping. One run is never assumed sufficient — every repetition
keeps its own identity even under temperature=0, since determinism at the model level
doesn't guarantee determinism at the environment/browser level.
"""
from __future__ import annotations

from dataclasses import dataclass

from .statistics_utils import ConfidenceInterval, DescriptiveStats, bootstrap_confidence_interval, describe


@dataclass
class RepetitionConfig:
    repetitions: int
    seed: int | None = None  # meaningful for stochastic settings; recorded even at temperature=0


@dataclass
class RepeatedRunResult:
    stats: DescriptiveStats
    bootstrap_ci: ConfidenceInterval


def aggregate_repeated_runs(values: list[float], confidence: float = 0.95, seed: int | None = None) -> RepeatedRunResult:
    return RepeatedRunResult(
        stats=describe(values),
        bootstrap_ci=bootstrap_confidence_interval(values, confidence=confidence, seed=seed),
    )
