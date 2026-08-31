"""L3-v1 — dynamic trajectory-level guardrail.

Monitors the episode's own recorded history (never hidden task state) for two
evidence-based drift signals, each logged with trigger/reason/evidence:

1. Repeated action: the proposed action exactly matches the last executed action
   (action type + target) — a stuck/looping pattern. Intervenes by substituting a
   "wait" to break the loop without guessing at what the agent "meant."
2. Excessive steps: the episode has run at least EXCESSIVE_STEPS_THRESHOLD steps
   without finishing. Intervenes by forcing "finish" to cap runaway trajectories.

No opaque correction: every intervention is a plain, fixed substitution, never a
model-generated "fix," and always logged with the evidence that triggered it.
"""
from __future__ import annotations

import json
from typing import Any

from .interface import GuardrailDecision, GuardrailResult

EXCESSIVE_STEPS_THRESHOLD = 5


class L3DynamicGuardrail:
    name = "L3_dynamic_guardrail"
    VERSION = "L3-v1"

    def evaluate(self, *, context: dict[str, Any]) -> GuardrailResult:
        action = context["proposed_action"]
        history = context["history"]
        step_number = context["step_number"]
        metadata = {"guardrail_version": self.VERSION}

        # Checked before the repeated-action rule below: if both conditions hold (e.g.
        # the agent is stuck repeating the same "wait"), forcing completion must win —
        # otherwise repeated-action would keep substituting "wait" for "wait" forever
        # and the trajectory would never actually escape via this guardrail.
        if step_number >= EXCESSIVE_STEPS_THRESHOLD and action.action != "finish":
            return GuardrailResult(
                decision=GuardrailDecision.MODIFY,
                intervention_type="modify",
                reason="excessive_steps_trajectory_drift_forced_completion",
                confidence=0.7,
                modified_content=json.dumps({"action": "finish"}),
                metadata={
                    **metadata,
                    "trigger": "excessive_steps",
                    "evidence": {"step_number": step_number, "threshold": EXCESSIVE_STEPS_THRESHOLD},
                },
            )

        if history:
            last_final = history[-1].action.get("final", {})
            if last_final.get("action") == action.action and last_final.get("target") == action.target:
                return GuardrailResult(
                    decision=GuardrailDecision.MODIFY,
                    intervention_type="modify",
                    reason="repeated_action_pattern_detected",
                    confidence=0.85,
                    modified_content=json.dumps({"action": "wait"}),
                    metadata={
                        **metadata,
                        "trigger": "repeated_action",
                        "evidence": {"step_number": step_number, "repeated": last_final},
                    },
                )

        return GuardrailResult(decision=GuardrailDecision.ALLOW, metadata=metadata)
