"""MockEnvironment — NOT ChildAgentEval.

Exists solely to exercise the Agent/Environment wiring (observe -> decide -> execute ->
new observation -> ... -> finish) without a browser, a network call, or any benchmark
content. Its trivial "click a button, type text, finish" interaction must never be
described as, or included in, benchmark results.
"""
from __future__ import annotations

from typing import Any

from ..observation import Observation
from .base import ActionResult, TaskSpec


class MockEnvironment:
    def __init__(self) -> None:
        self._button_clicked = False
        self._typed_text: str | None = None
        self._closed = False
        self._task: TaskSpec | None = None

    def reset(self, task: TaskSpec) -> Observation:
        self._task = task
        self._button_clicked = False
        self._typed_text = None
        self._closed = False
        return self._observation(done=False)

    def execute_action(self, action: Any) -> ActionResult:
        if self._closed:
            return ActionResult(success=False, observation=self._observation(done=True), error="environment is closed")

        kind = getattr(action, "action", None)
        if kind == "click" and getattr(action, "target", None) == "mock_button":
            self._button_clicked = True
            return ActionResult(success=True, observation=self._observation(done=False))
        if kind == "type" and getattr(action, "target", None) == "mock_input":
            self._typed_text = action.text
            return ActionResult(success=True, observation=self._observation(done=False))
        if kind == "wait":
            return ActionResult(success=True, observation=self._observation(done=False))
        if kind == "finish":
            return ActionResult(success=True, observation=self._observation(done=True))

        return ActionResult(
            success=False,
            observation=self._observation(done=False),
            error=f"MockEnvironment does not support action {kind!r} with the given target",
        )

    def close(self) -> None:
        self._closed = True

    def _observation(self, *, done: bool) -> Observation:
        return Observation(
            screenshot_ref=None,
            accessibility_tree={"note": "MockEnvironment has no real DOM"},
            page_metadata={"env": "mock", "task_id": self._task.task_id if self._task else None},
            available_elements=[
                {"id": "mock_button", "role": "button", "label": "Mock Button"},
                {"id": "mock_input", "role": "textbox", "label": "Mock Input"},
            ],
            task_state={"button_clicked": self._button_clicked, "typed_text": self._typed_text},
            done=done,
        )
