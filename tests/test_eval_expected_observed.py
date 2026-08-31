import pytest

from childagenteval_research.evaluation.expected_observed import (
    ExpectedResult,
    IncompatibleComparisonError,
    ObservedResult,
    compare_expected_observed,
)
from childagenteval_research.evaluation.reference_results import ReferenceResult


def test_expected_result_from_reference_row():
    ref = ReferenceResult(
        result_kind="reference_result", metric="total_composite_score", model="qwen3.5-27b",
        condition="baseline", target_age=7, value=0.32, source="arXiv:2605.17894",
        location="Table 2", confidence="medium", status="confirmed",
    )
    expected = ExpectedResult.from_reference(ref)
    assert expected.value == 0.32
    assert expected.confidence == "medium"


def test_compatible_comparison_reports_n_and_difference():
    expected = ExpectedResult(metric="score", model="qwen3.5-27b", condition="baseline", value=0.32, target_age=7)
    observed = ObservedResult(metric="score", model="qwen3.5-27b", condition="baseline", target_age=7,
                               values=(0.30, 0.31, 0.29, 0.33, 0.28))
    result = compare_expected_observed(expected, observed)
    assert result.n_observed == 5
    assert result.observed_mean == pytest.approx(0.302, abs=1e-9)
    assert result.absolute_difference == pytest.approx(0.302 - 0.32, abs=1e-9)
    assert result.effect_size_vs_expected is not None
    assert result.statistical_test is not None
    assert result.interpretation_status == "COMPARABLE"


def test_low_confidence_expected_value_flags_interpretation():
    expected = ExpectedResult(metric="score", model="gpt-5.4", condition="baseline", value=0.53, target_age=7, confidence="low")
    observed = ObservedResult(metric="score", model="gpt-5.4", condition="baseline", target_age=7, values=(0.5, 0.51))
    result = compare_expected_observed(expected, observed)
    assert "LOW_CONFIDENCE" in result.interpretation_status


def test_single_observed_run_flags_insufficient_data():
    expected = ExpectedResult(metric="score", model="qwen3.5-27b", condition="baseline", value=0.32, target_age=7)
    observed = ObservedResult(metric="score", model="qwen3.5-27b", condition="baseline", target_age=7, values=(0.30,))
    result = compare_expected_observed(expected, observed)
    assert result.n_observed == 1
    assert result.effect_size_vs_expected is None
    assert result.statistical_test is None
    assert "INSUFFICIENT" in result.interpretation_status


def test_zero_observed_runs_raises_rather_than_dividing_by_zero():
    expected = ExpectedResult(metric="score", model="qwen3.5-27b", condition="baseline", value=0.32, target_age=7)
    observed = ObservedResult(metric="score", model="qwen3.5-27b", condition="baseline", target_age=7, values=())
    with pytest.raises(IncompatibleComparisonError):
        compare_expected_observed(expected, observed)


def test_metric_mismatch_raises():
    expected = ExpectedResult(metric="score_a", model="m", condition="baseline", value=0.5)
    observed = ObservedResult(metric="score_b", model="m", condition="baseline", values=(0.5,))
    with pytest.raises(IncompatibleComparisonError):
        compare_expected_observed(expected, observed)


def test_age_mismatch_raises():
    expected = ExpectedResult(metric="score", model="m", condition="baseline", value=0.5, target_age=7)
    observed = ObservedResult(metric="score", model="m", condition="baseline", values=(0.5,), target_age=10)
    with pytest.raises(IncompatibleComparisonError):
        compare_expected_observed(expected, observed)


def test_relative_difference_none_when_expected_value_is_zero():
    expected = ExpectedResult(metric="score", model="m", condition="baseline", value=0.0)
    observed = ObservedResult(metric="score", model="m", condition="baseline", values=(0.1, 0.2))
    result = compare_expected_observed(expected, observed)
    assert result.relative_difference is None
