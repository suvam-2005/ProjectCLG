"""Generic Playwright-driven browser environment adapter.

Deliberately contains no ChildAgentEval-specific selectors, URLs, or task logic — we do
not have the official benchmark implementation (see docs/phase0_findings.md). This
class is the plug-in point: once official access is granted, either this adapter is
driven with the official task URLs/selectors via `TaskSpec.metadata`, or a dedicated
`OfficialChildAgentEvalAdapter` is added alongside it implementing the same
`Environment` protocol (see environment/base.py).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..observation import Observation
from .base import ActionResult, TaskSpec

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # playwright package or browser binaries not installed
    sync_playwright = None


class PlaywrightEnvironmentAdapter:
    def __init__(self, headless: bool = True, dom_assisted: bool = True, screenshots_dir: Path | None = None):
        self.headless = headless
        self.dom_assisted = dom_assisted
        self.screenshots_dir = screenshots_dir
        self._playwright = None
        self._browser = None
        self._page = None
        self._task: TaskSpec | None = None
        self._step = 0

    def reset(self, task: TaskSpec) -> Observation:
        start_url = task.metadata.get("start_url")
        if not start_url:
            raise ValueError(
                "PlaywrightEnvironmentAdapter requires task.metadata['start_url']; "
                "this generic adapter has no built-in benchmark URLs"
            )
        if sync_playwright is None:
            raise RuntimeError("playwright is not installed/initialized — run `playwright install`")

        self._task = task
        self._step = 0
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._page = self._browser.new_page()
        self._page.goto(start_url)
        return self._build_observation(done=False)

    def execute_action(self, action: Any) -> ActionResult:
        try:
            self._dispatch(action)
        except Exception as e:
            return ActionResult(success=False, observation=self._build_observation(done=False), error=str(e))
        done = action.action == "finish"
        return ActionResult(success=True, observation=self._build_observation(done=done))

    def _dispatch(self, action: Any) -> None:
        kind = action.action
        if kind == "click":
            self._page.click(action.target)
        elif kind == "type":
            self._page.fill(action.target, action.text)
        elif kind == "select":
            self._page.select_option(action.target, action.value)
        elif kind == "scroll":
            delta = 500 if action.direction == "down" else -500
            self._page.mouse.wheel(0, delta)
        elif kind == "keypress":
            self._page.keyboard.press(action.key)
        elif kind == "wait":
            self._page.wait_for_timeout(250)
        elif kind == "finish":
            pass
        else:
            raise ValueError(f"unsupported action type: {kind!r}")

    def _build_observation(self, *, done: bool) -> Observation:
        screenshot_ref = None
        if self.screenshots_dir is not None:
            self.screenshots_dir.mkdir(parents=True, exist_ok=True)
            screenshot_ref = str(self.screenshots_dir / f"step_{self._step:04d}.png")
            self._page.screenshot(path=screenshot_ref)
        self._step += 1

        # Playwright's legacy page.accessibility API was removed; aria_snapshot() on the
        # root element is the current equivalent (returns a YAML-like string, not a dict).
        accessibility_tree = self._page.locator("body").aria_snapshot() if self.dom_assisted else None

        return Observation(
            screenshot_ref=screenshot_ref,
            accessibility_tree=accessibility_tree,
            page_metadata={"url": self._page.url},
            available_elements=[],  # left generic; an official adapter fills this from permitted DOM info
            task_state=None,  # this generic adapter never invents task-state
            done=done,
        )

    def close(self) -> None:
        """Idempotent — safe to call more than once (e.g. once explicitly in a test and
        again from fixture teardown)."""
        if self._page is not None:
            self._page.close()
            self._page = None
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
