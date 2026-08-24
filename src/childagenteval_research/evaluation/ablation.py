"""Ablation variant identifiers for the future R3 dynamic guardrail. No guardrail logic
lives here — this only gives the comparison framework stable keys to group by once
ablations exist.
"""
from __future__ import annotations

from enum import Enum


class R3AblationVariant(str, Enum):
    FULL = "full_dynamic_guardrail"
    WITHOUT_MEMORY_CONTROL = "without_memory_control"
    WITHOUT_REASONING_CONTROL = "without_reasoning_control"
    WITHOUT_PLANNING_CONTROL = "without_planning_control"
    WITHOUT_OUTPUT_CONTROL = "without_output_control"
    WITHOUT_TRAJECTORY_MONITORING = "without_trajectory_monitoring"


IMPLEMENTED_ABLATIONS = frozenset()  # none yet — R3 itself isn't implemented
