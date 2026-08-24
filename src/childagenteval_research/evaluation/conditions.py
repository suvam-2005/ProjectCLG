"""The four research conditions. Only configuration/measurement identity is defined
here — none of R1-R3's guardrail algorithms are implemented (that's Phase 4+). This
module exists so metrics/analysis code has a stable, typed thing to key results on.
"""
from __future__ import annotations

from enum import Enum


class ResearchCondition(str, Enum):
    R0_ORIGINAL_BASELINE = "R0_original_baseline"   # standard age prompting, no guardrail
    R1_OUTPUT_GUARDRAIL = "R1_output_guardrail"       # observes proposed output before return
    R2_ACTION_GUARDRAIL = "R2_action_guardrail"       # evaluates proposed actions before execution
    R3_DYNAMIC_GUARDRAIL = "R3_dynamic_guardrail"     # trajectory-level monitoring + intervention


# R0 is the only condition with an implementation today (Phase 2's L0 == R0's harness
# wiring, modulo the still-missing official benchmark content). R1-R3 are declared here
# purely as identifiers for the evaluation framework to group results by.
IMPLEMENTED_CONDITIONS = frozenset({ResearchCondition.R0_ORIGINAL_BASELINE})

STANDARD_COMPARISONS: tuple[tuple[ResearchCondition, ResearchCondition], ...] = (
    (ResearchCondition.R0_ORIGINAL_BASELINE, ResearchCondition.R1_OUTPUT_GUARDRAIL),
    (ResearchCondition.R0_ORIGINAL_BASELINE, ResearchCondition.R2_ACTION_GUARDRAIL),
    (ResearchCondition.R0_ORIGINAL_BASELINE, ResearchCondition.R3_DYNAMIC_GUARDRAIL),
    (ResearchCondition.R1_OUTPUT_GUARDRAIL, ResearchCondition.R2_ACTION_GUARDRAIL),
    (ResearchCondition.R2_ACTION_GUARDRAIL, ResearchCondition.R3_DYNAMIC_GUARDRAIL),
)
