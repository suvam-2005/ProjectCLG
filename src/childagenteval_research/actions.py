"""Generic structured-action schema for agent <-> environment communication.

Action *kinds* here are generic (click/type/select/scroll/keypress/wait/finish) because
the official ChildAgentEval action set is not publicly documented (see
docs/phase0_findings.md). Once the official benchmark is available, its environment
adapter is responsible for translating these generic actions (or extending this schema)
to whatever the real interface requires — this module must not be changed to encode
benchmark-specific assumptions.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

VALID_ACTION_TYPES = {"click", "type", "select", "scroll", "keypress", "wait", "finish"}

# Fields required for each action type, beyond the common "action" field.
REQUIRED_FIELDS = {
    "click": {"target"},
    "type": {"target", "text"},
    "select": {"target", "value"},
    "scroll": {"direction"},
    "keypress": {"key"},
    "wait": set(),
    "finish": set(),
}


class ActionSource(str, Enum):
    MODEL = "model"                       # parsed successfully from the model's own output
    MALFORMED_RECOVERY = "malformed_recovery"  # model output failed validation; safe fallback used


@dataclass
class Action:
    action: str
    target: str | None = None
    text: str | None = None
    value: str | None = None
    direction: str | None = None
    key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    source: ActionSource = ActionSource.MODEL

    def to_dict(self) -> dict[str, Any]:
        d = {
            "action": self.action,
            "target": self.target,
            "text": self.text,
            "value": self.value,
            "direction": self.direction,
            "key": self.key,
            "metadata": self.metadata,
            "source": self.source.value,
        }
        return {k: v for k, v in d.items() if v is not None and v != {}}


class ActionValidationError(ValueError):
    pass


def parse_action(raw_text: str) -> Action:
    """Parse and validate a model's raw text output against the action schema.

    Raises ActionValidationError on any malformed input — the caller (agent loop) is
    responsible for applying the fixed, minimal recovery action; this function never
    guesses at the model's intent.
    """
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ActionValidationError(f"response is not valid JSON: {e}") from e

    if not isinstance(payload, dict):
        raise ActionValidationError(f"expected a JSON object, got {type(payload).__name__}")

    action_type = payload.get("action")
    if action_type not in VALID_ACTION_TYPES:
        raise ActionValidationError(
            f"unknown or missing action type {action_type!r}; must be one of {sorted(VALID_ACTION_TYPES)}"
        )

    missing = REQUIRED_FIELDS[action_type] - payload.keys()
    if missing:
        raise ActionValidationError(f"action {action_type!r} missing required field(s): {sorted(missing)}")

    known_keys = {"action", "target", "text", "value", "direction", "key", "metadata"}
    return Action(
        action=action_type,
        target=payload.get("target"),
        text=payload.get("text"),
        value=payload.get("value"),
        direction=payload.get("direction"),
        key=payload.get("key"),
        metadata=payload.get("metadata", {}) | {k: v for k, v in payload.items() if k not in known_keys},
        source=ActionSource.MODEL,
    )


def make_recovery_action(reason: str, raw_model_output: str) -> Action:
    """The single, fixed, minimal recovery action used whenever the model's output
    fails validation. Always the same shape — never an attempt to reinterpret or
    "fix" what the model meant, and never itself retried against the model."""
    return Action(
        action="wait",
        metadata={"reason": reason, "raw_model_output": raw_model_output},
        source=ActionSource.MALFORMED_RECOVERY,
    )
