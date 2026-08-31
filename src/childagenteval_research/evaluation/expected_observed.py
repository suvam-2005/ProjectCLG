"""EXPECTED_RESULT (what the paper reports) vs OBSERVED_RESULT (what we measure) vs
COMPARISON (brief §5). Comparison is refused, not fabricated, when the two sides aren't
compatible (different metric, different age/condition, or too little observed data).
"""
from __future__ import annotations

from dataclasses import dataclass

from .reference_results import ReferenceResult
from .statistics_utils import (
    ConfidenceInterval,
    EffectSize,
    TTestResult,
    confidence_interval,
    effect_size,
    welch_t_test,
)


@dataclass(frozen=True)
class ExpectedResult:
    metric: str
    model: str
    condition: str
    value: float
    target_age: int | None = None
    age_band: str | None = None
    subtest: str | None = None
    source: str = ""
    confidence: str = "unavailable"

    @classmethod
    def from_reference(cls, ref: ReferenceResult) -> "ExpectedResult":
        return cls(
            metric=ref.metric, model=ref.model, condition=ref.condition, value=ref.value,
            target_age=ref.target_age, age_band=ref.age_band, subtest=ref.subtest,
            source=f"{ref.source} ({ref.location})", confidence=ref.confidence,
        )


@dataclass(frozen=True)
class ObservedResult:
    metric: str
    model: str
    condition: str
    values: tuple[float, ...]  # one per run/repetition — never collapsed before comparison
    target_age: int | None = None
    age_band: str | None = None
    subtest: str | None = None


class IncompatibleComparisonError(ValueError):
    pass


@dataclass
class ComparisonResult:
    expected: ExpectedResult
    observed: ObservedResult
    n_observed: int
    observed_mean: float
    absolute_difference: float
    relative_difference: float | None
    observed_ci: ConfidenceInterval
    effect_size_vs_expected: EffectSize | None
    statistical_test: TTestResult | None
    interpretation_status: str


def _check_compatible(expected: ExpectedResult, observed: ObservedResult) -> None:
    if expected.metric != observed.metric:
        raise IncompatibleComparisonError(f"metric mismatch: {expected.metric!r} vs {observed.metric!r}")
    if expected.model != observed.model:
        raise IncompatibleComparisonError(f"model mismatch: {expected.model!r} vs {observed.model!r}")
    if expected.condition != observed.condition:
        raise IncompatibleComparisonError(f"condition mismatch: {expected.condition!r} vs {observed.condition!r}")
    if expected.target_age != observed.target_age or expected.age_band != observed.age_band:
        raise IncompatibleComparisonError("age condition mismatch between expected and observed")
    if expected.subtest != observed.subtest:
        raise IncompatibleComparisonError(f"subtest mismatch: {expected.subtest!r} vs {observed.subtest!r}")


def compare_expected_observed(expected: ExpectedResult, observed: ObservedResult) -> ComparisonResult:
    """Raises IncompatibleComparisonError rather than silently computing a difference
    between values that don't refer to the same thing."""
    _check_compatible(expected, observed)

    n = len(observed.values)
    if n == 0:
        raise IncompatibleComparisonError("cannot compare against zero observed runs")

    observed_mean = sum(observed.values) / n
    absolute_difference = observed_mean - expected.value
    relative_difference = (absolute_difference / expected.value) if expected.value != 0 else None

    observed_ci = confidence_interval(list(observed.values))
    effect = effect_size(list(observed.values), [expected.value] * n) if n >= 2 else None
    ttest = welch_t_test(list(observed.values), [expected.value] * n) if n >= 2 else None

    if expected.confidence == "low":
        interpretation_status = "EXPECTED_VALUE_LOW_CONFIDENCE — comparison computed but not reliable evidence"
    elif n < 2:
        interpretation_status = "INSUFFICIENT_OBSERVED_RUNS — point estimate only, no interval/test possible"
    else:
        interpretation_status = "COMPARABLE"

    return ComparisonResult(
        expected=expected,
        observed=observed,
        n_observed=n,
        observed_mean=observed_mean,
        absolute_difference=absolute_difference,
        relative_difference=relative_difference,
        observed_ci=observed_ci,
        effect_size_vs_expected=effect,
        statistical_test=ttest,
        interpretation_status=interpretation_status,
    )
