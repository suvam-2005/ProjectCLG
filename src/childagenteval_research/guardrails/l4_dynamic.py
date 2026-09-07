"""L4-v2 — dynamic trajectory-level guardrail with immediate-finish on repeat.

Extends L3's two evidence-based drift signals (repeated action, excessive steps).
Excessive-steps handling is unchanged from L3 (same threshold, same forced-completion
substitution) so any accuracy/cost difference between L3 and L4 is attributable to the
repeated-action branch alone.

v1 of this guardrail (redirect to the next untried clickable target on repeat) was
found, by actually running it, to be unsound: scoring.py determines a multiple_choice
task's outcome from ONLY the last click (`click_targets_in_order[-1]`), and the
guardrail has no visibility into a task's interaction_kind (Guardrail.evaluate only
receives a TaskSpec, not the full TaskDefinition/success_condition — by design, so no
guardrail can ever see ground truth). A harmless repeat of an already-correct choice
(the model re-confirming, or stalling right after answering) was therefore
INDISTINGUISHABLE, to the guardrail, from a genuinely stuck loop on a wrong choice —
and redirecting to a different choice in the harmless case actively overwrote a correct
last-click with an incorrect one, regressing tasks that L0/L1/L2/L3 all answered
correctly. See data/independent_benchmark/raw/trajectories/L4/abstraction_age10_v1.jsonl
(pre-fix run, since replaced) for the observed failure.

v2 fixes this by never touching the DOM again once a repeat is detected: it forces
`finish` immediately instead of substituting a different click. This can only ever
preserve or shorten the trajectory that L0/L3 would have produced — it never changes
which click was submitted last, so it cannot regress a task that was already correct,
and for a genuinely stuck/wrong-answer loop it locks in the same (already wrong) answer
sooner, at lower cost, matching L3's efficiency framing without L3's residual
oscillation (L3's "wait" substitution stops being detected as a repeat on the very next
step, since the proposed click no longer matches the last *executed* action, "wait" —
so L3 keeps re-allowing the same real click and re-inserting "wait" every other step
until the excessive-steps threshold, rather than stopping right away). Verified against
every sequence_click task's success_condition: no task ever requires the same target
twice in a row, so forcing finish on a same-target repeat can never truncate a
legitimately-required repeat.

No opaque correction: every intervention is a plain, fixed substitution, never a
model-generated "fix," and always logged with the evidence that triggered it — same
house style as L1-L3.
"""
from __future__ import annotations

import json
from typing import Any

from .interface import GuardrailDecision, GuardrailResult

EXCESSIVE_STEPS_THRESHOLD = 5


class L4DynamicGuardrail:
    name = "L4_dynamic_guardrail"
    VERSION = "L4-v2"

    def evaluate(self, *, context: dict[str, Any]) -> GuardrailResult:
        action = context["proposed_action"]
        history = context["history"]
        step_number = context["step_number"]
        metadata = {"guardrail_version": self.VERSION}

        # Same precedence as L3 and for the same reason: forcing completion must win
        # over repeated-action handling once steps are excessive.
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
                    reason="repeated_action_forced_immediate_completion",
                    confidence=0.85,
                    modified_content=json.dumps({"action": "finish"}),
                    metadata={
                        **metadata,
                        "trigger": "repeated_action",
                        "evidence": {"step_number": step_number, "repeated": last_final},
                    },
                )

        return GuardrailResult(decision=GuardrailDecision.ALLOW, metadata=metadata)
