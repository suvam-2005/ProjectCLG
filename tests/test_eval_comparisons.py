import pytest

from childagenteval_research.evaluation.comparisons import (
    ConditionResults,
    compare_conditions,
    compare_standard_pairs,
)


def test_compare_conditions_reports_mean_difference_and_n_on_both_sides():
    r0 = ConditionResults(
        condition="R0", performance_scores=[0.5, 0.6], alignment_scores=[0.3, 0.4],
        intervention_rates=[0.0, 0.0], trajectory_lengths=[5, 6], total_tokens=[100, 120], costs_usd=[0.01, 0.012],
    )
    r1 = ConditionResults(
        condition="R1", performance_scores=[0.4, 0.5], alignment_scores=[0.7, 0.8],
        intervention_rates=[0.3, 0.4], trajectory_lengths=[8, 9], total_tokens=[150, 160], costs_usd=[0.02, 0.021],
    )
    comparison = compare_conditions(r0, r1)
    assert comparison.condition_a == "R0"
    assert comparison.condition_b == "R1"
    assert comparison.task_performance.a_stats.n == 2
    assert comparison.task_performance.b_stats.n == 2
    assert comparison.task_performance.mean_difference == pytest.approx(-0.1)
    assert comparison.alignment.mean_difference > 0
    assert comparison.intervention.mean_difference > 0


def test_compare_conditions_handles_empty_side_without_crashing():
    r0 = ConditionResults(condition="R0")
    r1 = ConditionResults(condition="R1", performance_scores=[0.5])
    comparison = compare_conditions(r0, r1)
    assert comparison.task_performance.a_stats.n == 0
    assert comparison.task_performance.mean_difference is None


def test_compare_standard_pairs_skips_missing_conditions():
    results = {"R0": ConditionResults(condition="R0", performance_scores=[0.5])}
    comparisons = compare_standard_pairs(results, [("R0", "R1"), ("R2", "R3")])
    assert comparisons == []
