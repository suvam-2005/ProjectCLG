"""The Environment protocol every adapter (mock, Playwright-generic, and eventually the
official ChildAgentEval adapter) must implement.

CONSTRAINT (do not weaken this): an adapter's Observation must never contain answer
keys, scoring rubrics, hidden backend state, or information about future tasks. Adapters
expose only what a human test-taker interacting with the same interface would see.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ..observation import Observation


@dataclass
class TaskSpec:
    """Minimal, adapter-agnostic description of what to run. Real benchmark task
    content (item text, target coordinates, etc.) belongs to the official adapter once
    available — this is intentionally empty of any invented benchmark content."""

    task_id: str
    subtest: str
    target_age: int
    metadata: dict[str, Any]


@dataclass
class ActionResult:
    success: bool
    observation: Observation
    error: str | None = None


class Environment(Protocol):
    """Lifecycle: reset(task) -> initial Observation; then repeated execute_action(...)
    -> ActionResult, each carrying the next Observation; close() when the episode ends."""

    def reset(self, task: TaskSpec) -> Observation: ...

    def execute_action(self, action: Any) -> ActionResult: ...

    def close(self) -> None: ...


class OfficialBenchmarkUnavailableError(RuntimeError):
    """Raised when code asks to run against the real ChildAgentEval benchmark before
    official access has been granted. See docs/phase0_findings.md."""
