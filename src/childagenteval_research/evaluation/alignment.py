"""Alignment distance interface: multiple candidate metrics, none chosen as final.

Only NORMALIZED_SCORE-kind dimensions shared by both profiles are currently comparable
— categorical/distribution/confidence-interval comparison is deferred rather than
guessed at with an invented formula. Euclidean and cosine are implemented as concrete
raw measurements; Mahalanobis, distributional, and learned-representation methods are
declared but intentionally not implemented yet (they require covariance/reference data
this project does not have).
"""
from __future__ import annotations

import math
from enum import Enum

from .profiles import CognitiveAlignmentResult, ObservedProfile, ProfileValueKind, TargetProfile


class AlignmentDistanceMethod(str, Enum):
    EUCLIDEAN = "euclidean"
    COSINE = "cosine"
    MAHALANOBIS = "mahalanobis"
    DISTRIBUTIONAL = "distributional"
    LEARNED_REPRESENTATION = "learned_representation"


NOT_YET_IMPLEMENTED = frozenset(
    {
        AlignmentDistanceMethod.MAHALANOBIS,
        AlignmentDistanceMethod.DISTRIBUTIONAL,
        AlignmentDistanceMethod.LEARNED_REPRESENTATION,
    }
)


def _comparable_normalized_score_vectors(
    target: TargetProfile, observed: ObservedProfile
) -> tuple[list[float], list[float], list[str]]:
    t_vec, o_vec, used_dims = [], [], []
    for dim in target.dimensions():
        if dim not in observed.values:
            continue
        tv, ov = target.values[dim], observed.values[dim]
        if tv.kind == ProfileValueKind.NORMALIZED_SCORE and ov.kind == ProfileValueKind.NORMALIZED_SCORE:
            t_vec.append(tv.normalized_score)
            o_vec.append(ov.normalized_score)
            used_dims.append(dim)
    return t_vec, o_vec, used_dims


def compute_alignment(
    target: TargetProfile,
    observed: ObservedProfile,
    method: AlignmentDistanceMethod,
    *,
    confidence: float | None = None,
    evaluator_source: str | None = None,
) -> CognitiveAlignmentResult:
    if method in NOT_YET_IMPLEMENTED:
        raise NotImplementedError(
            f"{method.value} alignment distance is not implemented yet — the interface "
            "is reserved so it can be added without changing callers"
        )

    t_vec, o_vec, used_dims = _comparable_normalized_score_vectors(target, observed)
    if not used_dims:
        return CognitiveAlignmentResult(
            target_profile=target,
            observed_profile=observed,
            overall_alignment=None,
            distance=None,
            distance_method=method.value,
            confidence=confidence,
            evaluator_source=evaluator_source,
        )

    if method == AlignmentDistanceMethod.EUCLIDEAN:
        distance = math.sqrt(sum((t - o) ** 2 for t, o in zip(t_vec, o_vec)))
    elif method == AlignmentDistanceMethod.COSINE:
        dot = sum(t * o for t, o in zip(t_vec, o_vec))
        norm_t = math.sqrt(sum(t * t for t in t_vec))
        norm_o = math.sqrt(sum(o * o for o in o_vec))
        if norm_t == 0 or norm_o == 0:
            distance = None
        else:
            distance = 1.0 - (dot / (norm_t * norm_o))
    else:
        raise ValueError(f"unhandled method: {method!r}")

    # Per-dimension alignment as a provisional convenience (1 - |difference|), valid
    # only under the assumption both scores are normalized to [0, 1]. Not an official
    # metric — analysis scripts are free to derive other formulations from the raw
    # target/observed values retained on the result.
    dimension_alignment = {dim: 1.0 - abs(t - o) for dim, t, o in zip(used_dims, t_vec, o_vec)}
    overall_alignment = sum(dimension_alignment.values()) / len(dimension_alignment)

    return CognitiveAlignmentResult(
        target_profile=target,
        observed_profile=observed,
        overall_alignment=overall_alignment,
        dimension_alignment=dimension_alignment,
        distance=distance,
        distance_method=method.value,
        confidence=confidence,
        evaluator_source=evaluator_source,
    )
