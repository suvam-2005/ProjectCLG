"""Independent age-alignment metric for the Independent Interactive Cognitive-Age
Benchmark. NOT the reference paper's proprietary/official alignment score — this is our
own, explicitly documented formula, built on the generic profile/alignment machinery
from evaluation/profiles.py and evaluation/alignment.py.

TARGET PROFILE (documented formula, not a clinical norm): for each of our 8
INDEPENDENT_BENCHMARK_DIMENSIONS, the expected normalized score at a given age is a
simple linear interpolation between a floor at age 7 and a ceiling at age 16:

    expected(age) = FLOOR + (CEILING - FLOOR) * (age - 7) / (16 - 7)

This encodes only the modeling assumption "capability on these original, age-tuned
items should tend to increase with age" — it is not derived from WISC norms or any
clinical data, and is explicitly PROVISIONAL.

OBSERVED PROFILE: the model's actual mean per-category (== per-dimension) task score at
that age/condition, from scoring.category_scores().
"""
from __future__ import annotations

from dataclasses import dataclass

from ..evaluation.alignment import AlignmentDistanceMethod, compute_alignment
from ..evaluation.profiles import CognitiveAlignmentResult, ObservedProfile, ProfileValue, ProfileValueKind, TargetProfile
from .task_schema import INDEPENDENT_BENCHMARK_DIMENSIONS

TARGET_PROFILE_FLOOR = 0.35
TARGET_PROFILE_CEILING = 0.95
MIN_AGE = 7
MAX_AGE = 16


def expected_score_for_age(age: int) -> float:
    fraction = (age - MIN_AGE) / (MAX_AGE - MIN_AGE)
    fraction = min(1.0, max(0.0, fraction))
    return TARGET_PROFILE_FLOOR + (TARGET_PROFILE_CEILING - TARGET_PROFILE_FLOOR) * fraction


def build_target_profile(age: int) -> TargetProfile:
    expected = expected_score_for_age(age)
    return TargetProfile(
        values={
            dim: ProfileValue(kind=ProfileValueKind.NORMALIZED_SCORE, normalized_score=expected)
            for dim in INDEPENDENT_BENCHMARK_DIMENSIONS
        },
        evaluator_source="independent_benchmark_target_profile_formula_v1",
    )


def build_observed_profile(category_scores: dict[str, float | None]) -> ObservedProfile:
    values = {
        dim: ProfileValue(kind=ProfileValueKind.NORMALIZED_SCORE, normalized_score=score)
        for dim, score in category_scores.items()
        if score is not None
    }
    return ObservedProfile(values=values, evaluator_source="independent_benchmark_observed_task_scores")


@dataclass(frozen=True)
class AgeAlignmentResult:
    age: int
    alignment: CognitiveAlignmentResult


def compute_age_alignment(
    age: int,
    category_scores: dict[str, float | None],
    method: AlignmentDistanceMethod = AlignmentDistanceMethod.EUCLIDEAN,
) -> AgeAlignmentResult:
    target = build_target_profile(age)
    observed = build_observed_profile(category_scores)
    return AgeAlignmentResult(age=age, alignment=compute_alignment(target, observed, method))
