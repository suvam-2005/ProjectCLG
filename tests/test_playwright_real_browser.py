"""Real-Chromium integration tests (Phase 2.5) — NOT mocked, unlike test_environment.py.

Runs the actual PlaywrightEnvironmentAdapter against fixtures/local_playwright_smoke_test
(LOCAL_PLAYWRIGHT_SMOKE_TEST — an original static page, not ChildAgentEval, not
WISC-derived). Requires `playwright install chromium` to have been run once. Makes no
network calls and never touches OpenRouter.
"""
from pathlib import Path

import pytest

from childagenteval_research.actions import Action
from childagenteval_research.environment.base import TaskSpec
from childagenteval_research.environment.playwright_adapter import PlaywrightEnvironmentAdapter

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "local_playwright_smoke_test" / "index.html"
START_URL = FIXTURE_PATH.resolve().as_uri()


def make_task() -> TaskSpec:
    return TaskSpec(
        task_id="local_playwright_smoke_test",
        subtest="infra_smoke_test",
        target_age=0,  # not a real ChildAgentEval subtest/age; infra check only
        metadata={"start_url": START_URL},
    )


@pytest.fixture
def adapter():
    a = PlaywrightEnvironmentAdapter(headless=True, dom_assisted=True)
    yield a
    a.close()


def test_real_chromium_launches_and_loads_local_fixture(adapter):
    obs = adapter.reset(make_task())
    assert obs.done is False
    assert obs.page_metadata["url"] == START_URL


def test_real_accessibility_snapshot_is_retrievable(adapter):
    obs = adapter.reset(make_task())
    assert obs.accessibility_tree is not None
    assert isinstance(obs.accessibility_tree, str)
    assert "button" in obs.accessibility_tree.lower()


def test_real_screenshot_capture(tmp_path):
    adapter = PlaywrightEnvironmentAdapter(headless=True, screenshots_dir=tmp_path)
    try:
        adapter.reset(make_task())
        shots = list(tmp_path.glob("*.png"))
        assert len(shots) == 1
        assert shots[0].stat().st_size > 0
    finally:
        adapter.close()


def test_real_click_type_select_mutate_the_actual_page(adapter):
    adapter.reset(make_task())

    result = adapter.execute_action(Action(action="click", target="#start_button"))
    assert result.success is True
    assert adapter._page.get_attribute("#status", "data-state") == "started"

    result = adapter.execute_action(Action(action="type", target="#answer_input", text="hello smoke test"))
    assert result.success is True
    assert adapter._page.input_value("#answer_input") == "hello smoke test"

    result = adapter.execute_action(Action(action="select", target="#choice_select", value="a"))
    assert result.success is True
    assert adapter._page.eval_on_selector("#choice_select", "el => el.value") == "a"


def test_real_finish_button_click_flips_page_completion_indicator(adapter):
    adapter.reset(make_task())
    assert adapter._page.text_content("#status") == "not_started"

    adapter.execute_action(Action(action="click", target="#finish_button"))
    assert adapter._page.text_content("#status") == "completed"


def test_real_agent_finish_action_marks_episode_done_without_touching_page(adapter):
    adapter.reset(make_task())
    result = adapter.execute_action(Action(action="finish"))
    assert result.observation.done is True


def test_real_browser_closes_cleanly(adapter):
    adapter.reset(make_task())
    adapter.close()  # should not raise; fixture's own teardown calls it again — must be idempotent-safe
