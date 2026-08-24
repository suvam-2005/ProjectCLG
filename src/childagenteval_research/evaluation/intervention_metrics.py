"""Intervention metrics for R1-R3. No guardrail algorithm lives here — this only
aggregates whatever intervention events a (future) guardrail records.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class InterventionEvent:
    step_number: int
    intervention_type: str | None  # None means the guardrail allowed the action unchanged
    reason: str | None = None
    confidence: float | None = None
    latency_s: float | None = None
    was_replan: bool = False


@dataclass
class InterventionSummary:
    intervention_count: int
    opportunities: int
    accepted_action_count: int
    rejected_action_count: int
    modified_output_count: int
    replan_count: int
    intervention_latencies_s: list[float] = field(default_factory=list)

    @property
    def intervention_rate(self) -> float | None:
        if self.opportunities == 0:
            return None
        return self.intervention_count / self.opportunities


def summarize_interventions(events: list[InterventionEvent], opportunities: int) -> InterventionSummary:
    interventions = [e for e in events if e.intervention_type is not None]
    return InterventionSummary(
        intervention_count=len(interventions),
        opportunities=opportunities,
        accepted_action_count=sum(1 for e in events if e.intervention_type is None),
        rejected_action_count=sum(1 for e in interventions if e.intervention_type == "reject"),
        modified_output_count=sum(1 for e in interventions if e.intervention_type == "modify"),
        replan_count=sum(1 for e in interventions if e.was_replan),
        intervention_latencies_s=[e.latency_s for e in interventions if e.latency_s is not None],
    )


def unnecessary_intervention_rate(
    interventions: list[InterventionEvent],
    posthoc_evaluator: Callable[[InterventionEvent], bool] | None,
) -> float | None:
    """posthoc_evaluator(event) -> True if the pre-intervention action would have been
    accepted by a valid, independent post-hoc evaluator. Returns None — never a
    fabricated 0 — when no such evaluator is supplied or there were no interventions to
    evaluate."""
    if posthoc_evaluator is None or not interventions:
        return None
    would_have_been_fine = sum(1 for e in interventions if posthoc_evaluator(e))
    return would_have_been_fine / len(interventions)
