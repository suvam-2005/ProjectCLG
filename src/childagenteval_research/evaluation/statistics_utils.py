"""Generic statistical utilities. Every result dataclass carries its sample size(s) —
never hide N. No function here silently applies a significance test to a sample too
small for it to mean anything; callers must look at `n` themselves before interpreting
a p-value, and confidence-interval functions return None rather than a number when
there isn't enough data to compute variance (n < 2). Pure standard library — no numpy/
scipy dependency.
"""
from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass, field
from typing import Callable, Sequence


@dataclass
class DescriptiveStats:
    n: int
    mean: float | None
    median: float | None
    stdev: float | None
    minimum: float | None
    maximum: float | None


def describe(values: Sequence[float]) -> DescriptiveStats:
    n = len(values)
    if n == 0:
        return DescriptiveStats(n=0, mean=None, median=None, stdev=None, minimum=None, maximum=None)
    return DescriptiveStats(
        n=n,
        mean=statistics.mean(values),
        median=statistics.median(values),
        stdev=statistics.stdev(values) if n >= 2 else None,
        minimum=min(values),
        maximum=max(values),
    )


@dataclass
class ConfidenceInterval:
    n: int
    point_estimate: float | None
    low: float | None
    high: float | None
    confidence: float
    method: str


_Z_BY_CONFIDENCE = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}


def confidence_interval(values: Sequence[float], confidence: float = 0.95) -> ConfidenceInterval:
    """Normal-approximation CI of the mean. An approximation, not an exact Student's-t
    interval — treat cautiously for small n, which is exactly why n is always reported
    alongside it."""
    n = len(values)
    if n < 2:
        return ConfidenceInterval(n=n, point_estimate=statistics.mean(values) if n else None,
                                   low=None, high=None, confidence=confidence, method="normal_approx")
    z = _Z_BY_CONFIDENCE.get(confidence)
    if z is None:
        raise ValueError(f"unsupported confidence level {confidence!r}; supported: {sorted(_Z_BY_CONFIDENCE)}")
    m = statistics.mean(values)
    stderr = statistics.stdev(values) / math.sqrt(n)
    return ConfidenceInterval(n=n, point_estimate=m, low=m - z * stderr, high=m + z * stderr,
                               confidence=confidence, method="normal_approx")


def bootstrap_confidence_interval(
    values: Sequence[float],
    confidence: float = 0.95,
    n_resamples: int = 2000,
    statistic: Callable[[Sequence[float]], float] = statistics.mean,
    seed: int | None = None,
) -> ConfidenceInterval:
    n = len(values)
    if n == 0:
        return ConfidenceInterval(n=0, point_estimate=None, low=None, high=None,
                                   confidence=confidence, method="bootstrap")
    rng = random.Random(seed)
    resample_stats = [statistic([values[rng.randrange(n)] for _ in range(n)]) for _ in range(n_resamples)]
    resample_stats.sort()
    lower_tail = (1 - confidence) / 2
    low = resample_stats[max(0, int(lower_tail * n_resamples))]
    high = resample_stats[min(n_resamples - 1, int((1 - lower_tail) * n_resamples) - 1)]
    return ConfidenceInterval(n=n, point_estimate=statistic(values), low=low, high=high,
                               confidence=confidence, method=f"bootstrap(n_resamples={n_resamples}, seed={seed})")


@dataclass
class EffectSize:
    n1: int
    n2: int
    cohens_d: float | None
    method: str = "cohens_d_pooled_sd"


def effect_size(sample1: Sequence[float], sample2: Sequence[float]) -> EffectSize:
    n1, n2 = len(sample1), len(sample2)
    if n1 < 2 or n2 < 2:
        return EffectSize(n1=n1, n2=n2, cohens_d=None)
    m1, m2 = statistics.mean(sample1), statistics.mean(sample2)
    s1, s2 = statistics.stdev(sample1), statistics.stdev(sample2)
    pooled_sd = math.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2))
    if pooled_sd == 0:
        return EffectSize(n1=n1, n2=n2, cohens_d=None)
    return EffectSize(n1=n1, n2=n2, cohens_d=(m1 - m2) / pooled_sd)


@dataclass
class PairedComparisonResult:
    n: int
    mean_difference: float | None
    difference_ci: ConfidenceInterval
    cohens_d_paired: float | None


def paired_comparison(sample_a: Sequence[float], sample_b: Sequence[float]) -> PairedComparisonResult:
    if len(sample_a) != len(sample_b):
        raise ValueError("paired_comparison requires equal-length samples")
    differences = [a - b for a, b in zip(sample_a, sample_b)]
    n = len(differences)
    ci = confidence_interval(differences) if n else ConfidenceInterval(
        n=0, point_estimate=None, low=None, high=None, confidence=0.95, method="normal_approx"
    )
    mean_diff = statistics.mean(differences) if n else None
    cohens_d = None
    if n >= 2:
        sd = statistics.stdev(differences)
        if sd != 0:
            cohens_d = mean_diff / sd
    return PairedComparisonResult(n=n, mean_difference=mean_diff, difference_ci=ci, cohens_d_paired=cohens_d)


@dataclass
class RankCorrelationResult:
    n: int
    spearman_rho: float | None
    kendall_tau: float | None


def _ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = average_rank
        i = j + 1
    return ranks


def spearman_rank_correlation(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    n = len(xs)
    if n != len(ys) or n < 2:
        return None
    rx, ry = _ranks(xs), _ranks(ys)
    mean_rx, mean_ry = statistics.mean(rx), statistics.mean(ry)
    cov = sum((a - mean_rx) * (b - mean_ry) for a, b in zip(rx, ry))
    var_x = sum((a - mean_rx) ** 2 for a in rx)
    var_y = sum((b - mean_ry) ** 2 for b in ry)
    if var_x == 0 or var_y == 0:
        return None
    return cov / math.sqrt(var_x * var_y)


def kendalls_tau(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    n = len(xs)
    if n != len(ys) or n < 2:
        return None
    concordant = discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            sign_x = xs[j] - xs[i]
            sign_y = ys[j] - ys[i]
            product = sign_x * sign_y
            if product > 0:
                concordant += 1
            elif product < 0:
                discordant += 1
    total_pairs = n * (n - 1) / 2
    if total_pairs == 0:
        return None
    return (concordant - discordant) / total_pairs


def rank_correlation(xs: Sequence[float], ys: Sequence[float]) -> RankCorrelationResult:
    return RankCorrelationResult(
        n=len(xs), spearman_rho=spearman_rank_correlation(xs, ys), kendall_tau=kendalls_tau(xs, ys)
    )


@dataclass
class TTestResult:
    n1: int
    n2: int
    statistic: float | None
    p_value_two_tailed: float | None
    method: str


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2)))


def welch_t_test(sample1: Sequence[float], sample2: Sequence[float]) -> TTestResult:
    """Welch's t-test with a NORMAL-APPROXIMATION p-value (not the exact Student's-t
    distribution, which needs a special function this project avoids depending on
    numpy/scipy for). Adequate for the "is this compatible at all" question this
    project uses it for; not a substitute for a proper stats package in a publication.
    Returns None fields when there isn't enough data to compute a statistic."""
    n1, n2 = len(sample1), len(sample2)
    if n1 < 2 or n2 < 2:
        return TTestResult(n1=n1, n2=n2, statistic=None, p_value_two_tailed=None, method="welch_normal_approx")
    m1, m2 = statistics.mean(sample1), statistics.mean(sample2)
    v1, v2 = statistics.variance(sample1), statistics.variance(sample2)
    se = math.sqrt(v1 / n1 + v2 / n2)
    if se == 0:
        return TTestResult(n1=n1, n2=n2, statistic=None, p_value_two_tailed=None, method="welch_normal_approx")
    t_stat = (m1 - m2) / se
    p_value = 2 * (1 - _normal_cdf(abs(t_stat)))
    return TTestResult(n1=n1, n2=n2, statistic=t_stat, p_value_two_tailed=p_value, method="welch_normal_approx")


@dataclass
class MultipleComparisonResult:
    n_comparisons: int
    method: str
    adjusted_alpha: float | None = None
    adjusted_p_values: list[float] = field(default_factory=list)
    reject_null: list[bool] = field(default_factory=list)


def bonferroni_correction(p_values: Sequence[float], alpha: float = 0.05) -> MultipleComparisonResult:
    n = len(p_values)
    if n == 0:
        return MultipleComparisonResult(n_comparisons=0, method="bonferroni", adjusted_alpha=None)
    adjusted_alpha = alpha / n
    adjusted_p_values = [min(1.0, p * n) for p in p_values]
    return MultipleComparisonResult(
        n_comparisons=n,
        method="bonferroni",
        adjusted_alpha=adjusted_alpha,
        adjusted_p_values=adjusted_p_values,
        reject_null=[p < adjusted_alpha for p in p_values],
    )


def benjamini_hochberg_correction(p_values: Sequence[float], alpha: float = 0.05) -> MultipleComparisonResult:
    n = len(p_values)
    if n == 0:
        return MultipleComparisonResult(n_comparisons=0, method="benjamini_hochberg")
    indexed = sorted(range(n), key=lambda i: p_values[i])
    adjusted = [0.0] * n
    reject = [False] * n
    prev_adjusted = 1.0
    for rank_from_largest, idx in enumerate(reversed(indexed)):
        rank = n - rank_from_largest
        adjusted_p = min(prev_adjusted, p_values[idx] * n / rank)
        adjusted[idx] = adjusted_p
        prev_adjusted = adjusted_p
    threshold_crossed = False
    for rank, idx in reversed(list(enumerate(indexed, start=1))):
        if not threshold_crossed and p_values[idx] <= (rank / n) * alpha:
            threshold_crossed = True
        reject[idx] = threshold_crossed
    return MultipleComparisonResult(
        n_comparisons=n, method="benjamini_hochberg", adjusted_p_values=adjusted, reject_null=reject
    )
