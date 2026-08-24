import pytest

from childagenteval_research.evaluation.alignment import (
    NOT_YET_IMPLEMENTED,
    AlignmentDistanceMethod,
    compute_alignment,
)
from childagenteval_research.evaluation.profiles import (
    ObservedProfile,
    ProfileValue,
    ProfileValueKind,
    TargetProfile,
)


def test_profile_value_requires_its_kinds_field():
    ProfileValue(kind=ProfileValueKind.NORMALIZED_SCORE, normalized_score=0.5)  # ok
    with pytest.raises(ValueError):
        ProfileValue(kind=ProfileValueKind.NORMALIZED_SCORE)  # missing normalized_score


def test_profile_value_supports_categorical_distribution_and_ci():
    ProfileValue(kind=ProfileValueKind.CATEGORICAL, categorical_label="advanced")
    ProfileValue(kind=ProfileValueKind.DISTRIBUTION, distribution={"low": 0.2, "high": 0.8})
    ProfileValue(kind=ProfileValueKind.CONFIDENCE_INTERVAL, point_estimate=0.5, ci_low=0.4, ci_high=0.6)


def test_cognitive_profile_dimensions_not_hard_coded():
    profile = TargetProfile(values={"reasoning": ProfileValue(kind=ProfileValueKind.NORMALIZED_SCORE, normalized_score=0.7)})
    assert profile.dimensions() == ("reasoning",)


def make_profiles(target_scores: dict[str, float], observed_scores: dict[str, float]):
    target = TargetProfile(values={k: ProfileValue(kind=ProfileValueKind.NORMALIZED_SCORE, normalized_score=v) for k, v in target_scores.items()})
    observed = ObservedProfile(values={k: ProfileValue(kind=ProfileValueKind.NORMALIZED_SCORE, normalized_score=v) for k, v in observed_scores.items()})
    return target, observed


def test_euclidean_alignment_of_identical_profiles_is_zero_distance_full_alignment():
    target, observed = make_profiles({"reasoning": 0.5, "language": 0.8}, {"reasoning": 0.5, "language": 0.8})
    result = compute_alignment(target, observed, AlignmentDistanceMethod.EUCLIDEAN)
    assert result.distance == 0.0
    assert result.overall_alignment == 1.0
    assert result.dimension_alignment == {"reasoning": 1.0, "language": 1.0}


def test_euclidean_alignment_reflects_difference():
    target, observed = make_profiles({"reasoning": 1.0}, {"reasoning": 0.0})
    result = compute_alignment(target, observed, AlignmentDistanceMethod.EUCLIDEAN)
    assert result.distance == 1.0
    assert result.overall_alignment == 0.0


def test_cosine_alignment_of_parallel_vectors_is_zero_distance():
    target, observed = make_profiles({"reasoning": 0.5, "language": 0.5}, {"reasoning": 0.5, "language": 0.5})
    result = compute_alignment(target, observed, AlignmentDistanceMethod.COSINE)
    assert result.distance == pytest.approx(0.0, abs=1e-9)


def test_alignment_only_uses_comparable_normalized_score_dimensions():
    target = TargetProfile(values={
        "reasoning": ProfileValue(kind=ProfileValueKind.NORMALIZED_SCORE, normalized_score=0.5),
        "language": ProfileValue(kind=ProfileValueKind.CATEGORICAL, categorical_label="advanced"),
    })
    observed = ObservedProfile(values={
        "reasoning": ProfileValue(kind=ProfileValueKind.NORMALIZED_SCORE, normalized_score=0.5),
        "language": ProfileValue(kind=ProfileValueKind.CATEGORICAL, categorical_label="basic"),
    })
    result = compute_alignment(target, observed, AlignmentDistanceMethod.EUCLIDEAN)
    assert list(result.dimension_alignment.keys()) == ["reasoning"]


def test_no_comparable_dimensions_returns_none_not_a_fabricated_number():
    target = TargetProfile(values={"language": ProfileValue(kind=ProfileValueKind.CATEGORICAL, categorical_label="advanced")})
    observed = ObservedProfile(values={"language": ProfileValue(kind=ProfileValueKind.CATEGORICAL, categorical_label="basic")})
    result = compute_alignment(target, observed, AlignmentDistanceMethod.EUCLIDEAN)
    assert result.overall_alignment is None
    assert result.distance is None


@pytest.mark.parametrize("method", sorted(NOT_YET_IMPLEMENTED, key=lambda m: m.value))
def test_not_yet_implemented_methods_raise_clearly(method):
    target, observed = make_profiles({"reasoning": 0.5}, {"reasoning": 0.5})
    with pytest.raises(NotImplementedError):
        compute_alignment(target, observed, method)
