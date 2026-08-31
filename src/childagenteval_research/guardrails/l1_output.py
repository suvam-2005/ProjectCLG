"""L1-v1 — output guardrail.

Rationale: the agent is instructed (prompts.ACTION_SCHEMA_INSTRUCTIONS) to respond with
exactly one JSON action object and nothing else. A response padded with extra prose/
explanation is adult-like meta-commentary the benchmark never asked for. This guardrail
inspects only the model's RAW text output — never hidden task state, never the correct
answer — and either allows a clean response through, extracts a valid action from a
response that had extra text around it (MODIFY), or rejects a response with no
extractable valid action at all (REJECT). Every decision is logged with a reason.
"""
from __future__ import annotations

import re
from typing import Any

from ..actions import ActionValidationError, parse_action
from .interface import GuardrailDecision, GuardrailResult

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


class L1OutputGuardrail:
    name = "L1_output_guardrail"
    VERSION = "L1-v1"

    def evaluate(self, *, context: dict[str, Any]) -> GuardrailResult:
        raw_output = context.get("raw_model_output", "")
        metadata = {"guardrail_version": self.VERSION}

        if context.get("decision_error") is not None:
            # Already unparseable at all — Agent's own recovery already handles this;
            # L1 has nothing additional to add and must not double-intervene.
            return GuardrailResult(decision=GuardrailDecision.ALLOW, metadata=metadata)

        stripped = raw_output.strip()
        try:
            parse_action(stripped)
            return GuardrailResult(decision=GuardrailDecision.ALLOW, metadata=metadata)
        except ActionValidationError:
            pass

        match = _JSON_OBJECT_RE.search(raw_output)
        if match:
            candidate = match.group(0)
            try:
                parse_action(candidate)
                return GuardrailResult(
                    decision=GuardrailDecision.MODIFY,
                    intervention_type="modify",
                    reason="raw_output_contained_extra_text_around_a_valid_action_json",
                    confidence=0.9,
                    modified_content=candidate,
                    metadata=metadata,
                )
            except ActionValidationError:
                pass

        return GuardrailResult(
            decision=GuardrailDecision.REJECT,
            intervention_type="reject",
            reason="raw_output_not_reducible_to_a_single_valid_action_json",
            confidence=0.9,
            metadata=metadata,
        )
