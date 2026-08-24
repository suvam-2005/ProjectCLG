import pytest

from childagenteval_research.evaluation.statistics_utils import (
    benjamini_hochberg_correction,
    bonferroni_correction,
    bootstrap_confidence_interval,
    confidence_interval,
    describe,
    effect_size,
    kendalls_tau,
    paired_comparison,
    rank_correlation,
    spearman_rank_correlation,
)


def test_describe_reports_n_always():
    stats = describe([1.0, 2.0, 3.0])
    assert stats.n == 3
    assert stats.mean == 2.0
    assert stats.median == 2.0
    assert stats.stdev == pytest.approx(1.0)
    assert stats.minimum == 1.0
    assert stats.maximum == 3.0


def test_describe_empty_does_not_crash_and_reports_n_zero():
    stats = describe([])
    assert stats.n == 0
    assert stats.mean is None


def test_describe_single_value_has_no_stdev():
    stats = describe([5.0])
    assert stats.n == 1
    assert stats.stdev is None


def test_confidence_interval_none_below_n_2():
    ci = confidence_interval([5.0])
    assert ci.n == 1
    assert ci.low is None and ci.high is None


def test_confidence_interval_brackets_mean_for_normal_data():
    values = [10.0, 12.0, 11.0, 9.0, 13.0, 10.5, 11.5]
    ci = confidence_interval(values, confidence=0.95)
    assert ci.n == len(values)
    assert ci.low < ci.point_estimate < ci.high


def test_confidence_interval_rejects_unsupported_confidence():
    with pytest.raises(ValueError):
        confidence_interval([1.0, 2.0], confidence=0.5)


def test_bootstrap_confidence_interval_is_reproducible_with_seed():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    ci1 = bootstrap_confidence_interval(values, n_resamples=500, seed=42)
    ci2 = bootstrap_confidence_interval(values, n_resamples=500, seed=42)
    assert ci1.low == ci2.low
    assert ci1.high == ci2.high
    assert ci1.n == 5


def test_bootstrap_confidence_interval_empty_values():
    ci = bootstrap_confidence_interval([], seed=1)
    assert ci.n == 0
    assert ci.low is None


def test_effect_size_zero_for_identical_samples():
    result = effect_size([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert result.cohens_d == pytest.approx(0.0)
    assert result.n1 == 3 and result.n2 == 3


def test_effect_size_none_when_insufficient_data():
    result = effect_size([1.0], [1.0, 2.0])
    assert result.cohens_d is None


def test_paired_comparison_basic():
    result = paired_comparison([2.0, 3.0, 4.0], [1.0, 1.0, 1.0])
    assert result.n == 3
    assert result.mean_difference == pytest.approx(2.0)
    assert result.difference_ci.n == 3


def test_paired_comparison_requires_equal_length():
    with pytest.raises(ValueError):
        paired_comparison([1.0, 2.0], [1.0])


def test_spearman_perfect_positive_monotonic():
    assert spearman_rank_correlation([7, 10, 13, 16], [1, 2, 3, 4]) == pytest.approx(1.0)


def test_spearman_perfect_negative_monotonic():
    assert spearman_rank_correlation([7, 10, 13, 16], [4, 3, 2, 1]) == pytest.approx(-1.0)


def test_kendalls_tau_perfect_agreement():
    assert kendalls_tau([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)


def test_rank_correlation_reports_n():
    result = rank_correlation([7, 10, 13, 16], [1, 2, 3, 4])
    assert result.n == 4
    assert result.spearman_rho == pytest.approx(1.0)
    assert result.kendall_tau == pytest.approx(1.0)


def test_rank_correlation_none_for_tiny_or_mismatched_input():
    assert spearman_rank_correlation([1], [1]) is None
    assert spearman_rank_correlation([1, 2], [1]) is None


def test_bonferroni_correction_reports_n_and_scales_alpha():
    result = bonferroni_correction([0.01, 0.02, 0.2], alpha=0.05)
    assert result.n_comparisons == 3
    assert result.adjusted_alpha == pytest.approx(0.05 / 3)
    assert result.reject_null == [True, False, False]


def test_benjamini_hochberg_rejects_more_than_bonferroni_on_same_data():
    p_values = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205]
    bh = benjamini_hochberg_correction(p_values, alpha=0.05)
    bonf = bonferroni_correction(p_values, alpha=0.05)
    assert bh.n_comparisons == 8
    assert sum(bh.reject_null) >= sum(bonf.reject_null)


def test_multiple_comparison_correction_empty_input():
    result = bonferroni_correction([])
    assert result.n_comparisons == 0
    assert result.adjusted_alpha is None
