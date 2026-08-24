import pytest

from childagenteval_research.evaluation.age_trend_analysis import analyze_age_trend, monotonic_regression
from childagenteval_research.evaluation.per_age_analysis import group_by_age_and_condition, summarize_grouped
from childagenteval_research.evaluation.statistics_utils import describe


def test_group_by_age_and_condition_keeps_ages_separate():
    results = [
        {"age": 7, "condition": "R0", "score": 0.1},
        {"age": 7, "condition": "R1", "score": 0.2},
        {"age": 10, "condition": "R0", "score": 0.5},
    ]
    grouped = group_by_age_and_condition(results, lambda r: r["age"], lambda r: r["condition"])
    assert set(grouped.keys()) == {7, 10}
    assert set(grouped[7].keys()) == {"R0", "R1"}
    assert len(grouped[10]["R0"]) == 1


def test_summarize_grouped_applies_fn_per_cell_not_across_ages():
    grouped = {
        7: {"R0": [{"score": 0.1}, {"score": 0.3}]},
        10: {"R0": [{"score": 0.9}]},
    }
    summarized = summarize_grouped(grouped, lambda items: describe([i["score"] for i in items]))
    assert summarized[7]["R0"].n == 2
    assert summarized[10]["R0"].n == 1
    assert summarized[7]["R0"].mean != summarized[10]["R0"].mean


def test_analyze_age_trend_reports_n_and_correlation():
    result = analyze_age_trend({7: 0.1, 10: 0.4, 13: 0.7, 16: 0.9})
    assert result.n == 4
    assert result.ages == [7, 10, 13, 16]
    assert result.correlation.spearman_rho == pytest.approx(1.0)


def test_monotonic_regression_not_implemented_by_design():
    with pytest.raises(NotImplementedError):
        monotonic_regression([7, 10], [0.1, 0.2])
