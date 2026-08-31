"""Synthetic-data validation of the independent alignment metric (brief §9): must
behave sensibly before it's ever applied to real results. All values here are
[TEST DATA] — no real experiment results are used."""
import pytest

from childagenteval_research.benchmark.independent_alignment import (
    build_target_profile,
    compute_age_alignment,
    expected_score_for_age,
)
from childagenteval_research.benchmark.task_schema import INDEPENDENT_BENCHMARK_DIMENSIONS


def test_expected_score_increases_monotonically_with_age():
    scores = [expected_score_for_age(age) for age in (7, 10, 13, 16)]
    assert scores == sorted(scores)
    assert scores[0] < scores[-1]


def test_expected_score_clips_outside_the_defined_age_range():
    assert expected_score_for_age(5) == expected_score_for_age(7)
    assert expected_score_for_age(20) == expected_score_for_age(16)


def test_target_profile_covers_all_eight_dimensions():
    profile = build_target_profile(10)
    assert set(profile.dimensions()) == set(INDEPENDENT_BENCHMARK_DIMENSIONS)


def test_perfect_target_match_gives_high_alignment():
    age = 13
    expected = expected_score_for_age(age)
    perfect_scores = {dim: expected for dim in INDEPENDENT_BENCHMARK_DIMENSIONS}
    result = compute_age_alignment(age, perfect_scores)
    assert result.alignment.overall_alignment == pytest.approx(1.0, abs=1e-9)


def test_large_mismatch_gives_lower_alignment_than_perfect_match():
    age = 13
    expected = expected_score_for_age(age)
    perfect_scores = {dim: expected for dim in INDEPENDENT_BENCHMARK_DIMENSIONS}
    mismatched_scores = {dim: max(0.0, min(1.0, expected - 0.6)) for dim in INDEPENDENT_BENCHMARK_DIMENSIONS}

    perfect_alignment = compute_age_alignment(age, perfect_scores).alignment.overall_alignment
    mismatched_alignment = compute_age_alignment(age, mismatched_scores).alignment.overall_alignment

    assert mismatched_alignment < perfect_alignment


def test_random_uniform_behavior_is_not_artificially_high():
    # A model that behaves identically regardless of age-appropriate difficulty (e.g.
    # always ~0.5 mean score from effectively random multiple-choice guessing at ~4
    # options plus some sequence-click luck) should NOT score near-perfect alignment
    # for every age, especially where expected(age) is far from 0.5.
    random_like_scores = {dim: 0.5 for dim in INDEPENDENT_BENCHMARK_DIMENSIONS}

    alignment_age7 = compute_age_alignment(7, random_like_scores).alignment.overall_alignment  # expected ~0.35
    alignment_age16 = compute_age_alignment(16, random_like_scores).alignment.overall_alignment  # expected ~0.95

    assert alignment_age7 < 1.0
    assert alignment_age16 < 1.0
    # the mismatch (and thus the alignment penalty) should be larger at age 16, where
    # the gap between "random-ish" 0.5 and the age-16 target (0.95) is much bigger
    assert alignment_age16 < alignment_age7


def test_missing_dimensions_in_observed_do_not_crash_and_reduce_comparable_dims():
    age = 10
    partial_scores = {"reasoning": 0.6, "language": 0.5}  # only 2 of 8 dimensions
    result = compute_age_alignment(age, partial_scores)
    assert set(result.alignment.dimension_alignment.keys()) == {"reasoning", "language"}


def test_no_observed_scores_returns_none_alignment_not_a_fabricated_number():
    result = compute_age_alignment(10, {})
    assert result.alignment.overall_alignment is None
