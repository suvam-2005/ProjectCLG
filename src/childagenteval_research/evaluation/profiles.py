"""Cognitive profile representation.

PROVISIONAL: the seven dimension names below are placeholders inferred from the CHC
factors the paper mentions (Gc/Gf/Gv/WM/PSI-style groupings), NOT confirmed against the
official methodology, which is unavailable (docs/phase0_findings.md). A profile is a
plain dict of dimension name -> ProfileValue, not a fixed set of dataclass fields — so
the dimension set can be corrected once official access clarifies it, without changing
this module's shape.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

PROVISIONAL_COGNITIVE_DIMENSIONS: tuple[str, ...] = (
    "reasoning",
    "working_memory",
    "abstraction",
    "language",
    "visual_reasoning",
    "planning",
    "processing_behavior",
)


class ProfileValueKind(str, Enum):
    CATEGORICAL = "categorical"
    NORMALIZED_SCORE = "normalized_score"
    DISTRIBUTION = "distribution"
    CONFIDENCE_INTERVAL = "confidence_interval"


@dataclass
class ProfileValue:
    kind: ProfileValueKind
    categorical_label: str | None = None
    normalized_score: float | None = None
    distribution: dict[str, float] | None = None
    point_estimate: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None

    def __post_init__(self) -> None:
        present = {
            ProfileValueKind.CATEGORICAL: self.categorical_label is not None,
            ProfileValueKind.NORMALIZED_SCORE: self.normalized_score is not None,
            ProfileValueKind.DISTRIBUTION: self.distribution is not None,
            ProfileValueKind.CONFIDENCE_INTERVAL: self.point_estimate is not None,
        }
        if not present[self.kind]:
            raise ValueError(f"ProfileValue(kind={self.kind.value}) is missing its required field")


@dataclass
class CognitiveProfile:
    values: dict[str, ProfileValue] = field(default_factory=dict)
    evaluator_source: str | None = None  # who/what produced this profile, e.g. "human_rater_pair"

    def dimensions(self) -> tuple[str, ...]:
        return tuple(self.values.keys())

    def to_dict(self) -> dict[str, Any]:
        return {
            "values": {
                dim: {
                    "kind": v.kind.value,
                    "categorical_label": v.categorical_label,
                    "normalized_score": v.normalized_score,
                    "distribution": v.distribution,
                    "point_estimate": v.point_estimate,
                    "ci_low": v.ci_low,
                    "ci_high": v.ci_high,
                }
                for dim, v in self.values.items()
            },
            "evaluator_source": self.evaluator_source,
        }


class TargetProfile(CognitiveProfile):
    pass


class ObservedProfile(CognitiveProfile):
    pass


@dataclass
class CognitiveAlignmentResult:
    target_profile: TargetProfile
    observed_profile: ObservedProfile
    overall_alignment: float | None
    dimension_alignment: dict[str, float | None] = field(default_factory=dict)
    distance: float | None = None
    distance_method: str | None = None
    confidence: float | None = None
    evaluator_source: str | None = None
