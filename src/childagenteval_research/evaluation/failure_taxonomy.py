"""PROVISIONAL failure taxonomy — categories are placeholders pending validation against
the real environment/benchmark. `classify_failure` only assigns a category when it can
be read directly off our own recorded facts (a validation error, a guardrail decision);
everything requiring domain judgment (perception/reasoning/memory/etc.) is left
UNCATEGORIZED rather than guessed at.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Mapping


class FailureCategory(str, Enum):
    PERCEPTION_FAILURE = "perception_failure"
    ACTION_SELECTION_FAILURE = "action_selection_failure"
    REASONING_FAILURE = "reasoning_failure"
    MEMORY_FAILURE = "memory_failure"
    INSTRUCTION_FOLLOWING_FAILURE = "instruction_following_failure"
    TOOL_ENVIRONMENT_FAILURE = "tool_environment_failure"
    MALFORMED_OUTPUT = "malformed_output"
    TIMEOUT = "timeout"
    GUARDRAIL_INTERVENTION = "guardrail_intervention"
    BENCHMARK_SPECIFIC_FAILURE = "benchmark_specific_failure"
    UNCATEGORIZED = "uncategorized"


def classify_failure(record: Mapping[str, Any]) -> FailureCategory | None:
    """Returns None for a step with no failure at all. Only ever infers a category from
    facts already present in the trajectory record — never a guess about the model's
    internal reasoning.

    Guardrail intervention is checked ahead of the "did the environment call succeed"
    check: a guardrail's recovery action (e.g. a safe "wait") can itself succeed at the
    environment level, so success=True alone must not short-circuit past a real
    intervention.
    """
    action_result = record.get("action_result", {})
    error = record.get("error")
    success = action_result.get("success", True)
    guardrail_decision = record.get("action", {}).get("guardrail_decision")

    if error is None and success and guardrail_decision in (None, "allow"):
        return None

    if record.get("recovery") is not None and error:
        return FailureCategory.MALFORMED_OUTPUT

    if guardrail_decision in ("reject", "modify"):
        return FailureCategory.GUARDRAIL_INTERVENTION

    if action_result.get("error"):
        return FailureCategory.TOOL_ENVIRONMENT_FAILURE

    return FailureCategory.UNCATEGORIZED
