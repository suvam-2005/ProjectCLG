"""Observation representation passed from an Environment to the Agent.

Only information the environment adapter explicitly chooses to expose ends up here.
No adapter in this codebase may populate `task_state` with answer keys, scoring
information, hidden backend state, or future-task content — see the constraint in
environment/base.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Observation:
    screenshot_ref: str | None = None
    accessibility_tree: list[dict[str, Any]] | dict[str, Any] | str | None = None
    page_metadata: dict[str, Any] = field(default_factory=dict)
    available_elements: list[dict[str, Any]] = field(default_factory=list)
    task_state: dict[str, Any] | None = None
    done: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "screenshot_ref": self.screenshot_ref,
            "accessibility_tree": self.accessibility_tree,
            "page_metadata": self.page_metadata,
            "available_elements": self.available_elements,
            "task_state": self.task_state,
            "done": self.done,
        }
