"""Two distinct, non-interchangeable age concepts (see docs/phase0_findings.md):

- BASELINE_ANCHOR_AGES: single-year ages used by the paper's standard age-prompting
  baseline (R0) and, per the brief, by all research conditions unless stated otherwise.
- SKILL_GUIDED_AGE_BANDS: ranges used specifically by the paper's skill-guided
  condition. A result tagged with a band is never comparable to one tagged with an
  anchor age without an explicit, documented mapping — this module refuses to guess one.
"""
from __future__ import annotations

BASELINE_ANCHOR_AGES: tuple[int, ...] = (7, 10, 13, 16)
SKILL_GUIDED_AGE_BANDS: tuple[str, ...] = ("6-8", "9-11", "12-14", "15-17")


class AgeConditionMismatchError(ValueError):
    pass


def validate_anchor_age(age: int) -> int:
    if age not in BASELINE_ANCHOR_AGES:
        raise AgeConditionMismatchError(
            f"{age!r} is not one of the paper's baseline anchor ages {BASELINE_ANCHOR_AGES}; "
            "do not invent additional age groups"
        )
    return age


def validate_age_band(band: str) -> str:
    if band not in SKILL_GUIDED_AGE_BANDS:
        raise AgeConditionMismatchError(
            f"{band!r} is not one of the paper's skill-guided age bands {SKILL_GUIDED_AGE_BANDS}"
        )
    return band
