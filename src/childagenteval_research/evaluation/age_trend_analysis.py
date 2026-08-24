"""Is behavior age-ordered? Age -> score, tested for monotonicity. No single test is
picked as final — both rank correlation methods are reported; isotonic/monotonic
regression is deliberately not implemented (would need a real implementation choice
validated against the actual score distribution, which is unavailable).
"""
from __future__ import annotations

from dataclasses import dataclass

from .statistics_utils import RankCorrelationResult, rank_correlation


@dataclass
class AgeTrendResult:
    n: int
    ages: list[int]
    scores: list[float]
    correlation: RankCorrelationResult


def analyze_age_trend(age_to_score: dict[int, float]) -> AgeTrendResult:
    ages = sorted(age_to_score)
    scores = [age_to_score[a] for a in ages]
    return AgeTrendResult(n=len(ages), ages=ages, scores=scores, correlation=rank_correlation(ages, scores))


def monotonic_regression(ages: list[int], scores: list[float]) -> None:
    raise NotImplementedError(
        "Isotonic/monotonic regression is not implemented — the brief explicitly asks "
        "not to choose a final statistical test until the official benchmark's scoring "
        "distribution is known. Use analyze_age_trend()'s rank correlations for now."
    )
