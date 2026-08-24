"""Common guardrail interface. L1-L3 are not implemented yet (Phase 2-5) — L0 (no
guardrail) is the only active condition until it is validated as a clean control."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class GuardrailDecision(str, Enum):
    ALLOW = "allow"
    REJECT = "reject"
    MODIFY = "modify"


@dataclass
class GuardrailResult:
    decision: GuardrailDecision
    intervention_type: str | None = None
    reason: str | None = None
    confidence: float | None = None
    modified_content: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Guardrail(Protocol):
    """Every guardrail level (L1 output, L2 action, L3 dynamic) implements this."""

    name: str

    def evaluate(self, *, context: dict[str, Any]) -> GuardrailResult:
        ...


class NoGuardrail:
    """L0: control condition. Always allows, unmodified. Must stay this simple."""

    name = "L0_none"

    def evaluate(self, *, context: dict[str, Any]) -> GuardrailResult:
        return GuardrailResult(decision=GuardrailDecision.ALLOW, intervention_type=None)
