"""L2-v1 — action guardrail.

Inspects the parsed proposed action against the SAME observation the agent itself saw
(brief requirement: no privileged information). Two evidence-based rules, both logged:

1. Reject a "finish" issued as literally the first action of the episode, before any
   real interaction — a plausible impulsive shortcut, not a considered answer.
2. Reject click/type/select actions whose target isn't in the observation's own
   `available_elements` — an invalid or hallucinated selector, never a hidden-answer check.
"""
from __future__ import annotations

from typing import Any

from .interface import GuardrailDecision, GuardrailResult


class L2ActionGuardrail:
    name = "L2_action_guardrail"
    VERSION = "L2-v1"

    def evaluate(self, *, context: dict[str, Any]) -> GuardrailResult:
        action = context["proposed_action"]
        observation = context["observation"]
        step_number = context["step_number"]
        metadata = {"guardrail_version": self.VERSION}

        if action.action == "finish" and step_number == 0:
            return GuardrailResult(
                decision=GuardrailDecision.REJECT,
                intervention_type="reject",
                reason="premature_finish_before_any_interaction",
                confidence=1.0,
                metadata=metadata,
            )

        if action.action in ("click", "type", "select"):
            valid_targets = {el.get("id") for el in observation.available_elements}
            if action.target not in valid_targets:
                return GuardrailResult(
                    decision=GuardrailDecision.REJECT,
                    intervention_type="reject",
                    reason=f"target_not_in_available_elements:{action.target!r}",
                    confidence=1.0,
                    metadata=metadata,
                )

        return GuardrailResult(decision=GuardrailDecision.ALLOW, metadata=metadata)
