"""The four result categories (brief §8) — never mixed. A function that returns a
REFERENCE_RESULT must not also produce an OUR_RESULT, and vice versa."""
from __future__ import annotations

from enum import Enum


class ResultKind(str, Enum):
    REFERENCE_RESULT = "reference_result"        # reported by the original paper
    OUR_RESULT = "our_result"                     # any measurement from our own experiment
    REPRODUCTION_RESULT = "reproduction_result"   # our_result while attempting to replicate the paper's methodology
    GUARDRAIL_RESULT = "guardrail_result"         # our_result after introducing L1/L2/L3
