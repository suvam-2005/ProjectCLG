"""Pairwise condition comparison (R0 vs R1, R1 vs R2, etc.). Reports raw differences of
means alongside both sides' full descriptive stats — including n — never a bare delta.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .statistics_utils import DescriptiveStats, describe


@dataclass
class ConditionResults:
    condition: str
    performance_scores: list[float] = field(default_factory=list)
    alignment_scores: list[float] = field(default_factory=list)
    intervention_rates: list[float] = field(default_factory=list)
    trajectory_lengths: list[float] = field(default_factory=list)
    total_tokens: list[float] = field(default_factory=list)
    costs_usd: list[float] = field(default_factory=list)


@dataclass
class MetricComparison:
    a_stats: DescriptiveStats
    b_stats: DescriptiveStats
    mean_difference: float | None  # b - a


def _compare_metric(a_values: list[float], b_values: list[float]) -> MetricComparison:
    a_stats, b_stats = describe(a_values), describe(b_values)
    diff = (b_stats.mean - a_stats.mean) if (a_stats.mean is not None and b_stats.mean is not None) else None
    return MetricComparison(a_stats=a_stats, b_stats=b_stats, mean_difference=diff)


@dataclass
class ConditionComparisonResult:
    condition_a: str
    condition_b: str
    task_performance: MetricComparison
    alignment: MetricComparison
    intervention: MetricComparison
    trajectory: MetricComparison
    tokens: MetricComparison
    cost: MetricComparison


def compare_conditions(a: ConditionResults, b: ConditionResults) -> ConditionComparisonResult:
    return ConditionComparisonResult(
        condition_a=a.condition,
        condition_b=b.condition,
        task_performance=_compare_metric(a.performance_scores, b.performance_scores),
        alignment=_compare_metric(a.alignment_scores, b.alignment_scores),
        intervention=_compare_metric(a.intervention_rates, b.intervention_rates),
        trajectory=_compare_metric(a.trajectory_lengths, b.trajectory_lengths),
        tokens=_compare_metric(a.total_tokens, b.total_tokens),
        cost=_compare_metric(a.costs_usd, b.costs_usd),
    )


def compare_standard_pairs(
    results_by_condition: dict[str, ConditionResults],
    pairs: list[tuple[str, str]],
) -> list[ConditionComparisonResult]:
    comparisons = []
    for a_key, b_key in pairs:
        if a_key not in results_by_condition or b_key not in results_by_condition:
            continue
        comparisons.append(compare_conditions(results_by_condition[a_key], results_by_condition[b_key]))
    return comparisons
