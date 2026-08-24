"""Resolves the `environment.adapter` config value to a concrete Environment.

This is the single switch point for plugging in the real ChildAgentEval benchmark once
access is granted: add an `OfficialChildAgentEvalAdapter` implementing the `Environment`
protocol (base.py) and register it here under the "official_childagenteval" key. Until
then, requesting it raises OfficialBenchmarkUnavailableError rather than silently
falling back to a substitute.
"""
from __future__ import annotations

from pathlib import Path

from .base import Environment, OfficialBenchmarkUnavailableError
from .mock_environment import MockEnvironment
from .playwright_adapter import PlaywrightEnvironmentAdapter


def get_environment(adapter: str, *, headless: bool = True, screenshots_dir: Path | None = None) -> Environment:
    if adapter == "official_childagenteval":
        raise OfficialBenchmarkUnavailableError(
            "The official ChildAgentEval benchmark is not publicly available and access "
            "has not yet been granted (see docs/phase0_findings.md and "
            "docs/email_draft_to_authors.md). Refusing to substitute a locally built "
            "task set for it."
        )
    if adapter == "mock":
        return MockEnvironment()
    if adapter == "playwright_generic":
        return PlaywrightEnvironmentAdapter(headless=headless, screenshots_dir=screenshots_dir)
    raise ValueError(f"unknown environment adapter: {adapter!r}")
