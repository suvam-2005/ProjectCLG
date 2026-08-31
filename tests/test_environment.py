import pytest

from childagenteval_research.actions import Action
from childagenteval_research.environment import playwright_adapter
from childagenteval_research.environment.base import OfficialBenchmarkUnavailableError, TaskSpec
from childagenteval_research.environment.factory import get_environment
from childagenteval_research.environment.mock_environment import MockEnvironment
from childagenteval_research.environment.playwright_adapter import PlaywrightEnvironmentAdapter


def make_task(**overrides) -> TaskSpec:
    defaults = dict(task_id="t1", subtest="infra_test", target_age=10, metadata={})
    defaults.update(overrides)
    return TaskSpec(**defaults)


# ---- MockEnvironment ----

def test_mock_environment_reset_returns_initial_observation():
    env = MockEnvironment()
    obs = env.reset(make_task())
    assert obs.done is False
    assert any(e["id"] == "mock_button" for e in obs.available_elements)


def test_mock_environment_click_updates_state():
    env = MockEnvironment()
    env.reset(make_task())
    result = env.execute_action(Action(action="click", target="mock_button"))
    assert result.success is True
    assert result.observation.task_state["button_clicked"] is True


def test_mock_environment_type_updates_state():
    env = MockEnvironment()
    env.reset(make_task())
    result = env.execute_action(Action(action="type", target="mock_input", text="hi"))
    assert result.observation.task_state["typed_text"] == "hi"


def test_mock_environment_finish_marks_done():
    env = MockEnvironment()
    env.reset(make_task())
    result = env.execute_action(Action(action="finish"))
    assert result.observation.done is True


def test_mock_environment_unsupported_action_reports_failure_not_crash():
    env = MockEnvironment()
    env.reset(make_task())
    result = env.execute_action(Action(action="click", target="nonexistent"))
    assert result.success is False
    assert result.error is not None


def test_mock_environment_close_then_execute_reports_closed():
    env = MockEnvironment()
    env.reset(make_task())
    env.close()
    result = env.execute_action(Action(action="click", target="mock_button"))
    assert result.success is False
    assert "closed" in result.error


# ---- Environment factory ----

def test_factory_blocks_official_adapter():
    with pytest.raises(OfficialBenchmarkUnavailableError):
        get_environment("official_childagenteval")


def test_factory_returns_mock_environment():
    env = get_environment("mock")
    assert isinstance(env, MockEnvironment)


def test_factory_rejects_unknown_adapter():
    with pytest.raises(ValueError):
        get_environment("something_made_up")


# ---- PlaywrightEnvironmentAdapter (mocked browser; no real Chromium launch) ----

class FakePage:
    def __init__(self):
        self.url = "https://example.invalid/start"
        self.clicked = []
        self.filled = []
        self.closed = False

    def goto(self, url):
        self.url = url

    def click(self, target):
        self.clicked.append(target)

    def fill(self, target, text):
        self.filled.append((target, text))

    def select_option(self, target, value):
        pass

    @property
    def keyboard(self):
        page = self

        class _Keyboard:
            def press(self, key):
                page.clicked.append(f"key:{key}")

        return _Keyboard()

    @property
    def mouse(self):
        class _Mouse:
            def wheel(self, x, y):
                pass

        return _Mouse()

    def eval_on_selector_all(self, selector, expression):
        return [{"id": "#go", "tag": "button", "label": "Go"}]

    def locator(self, selector):
        class _Locator:
            def aria_snapshot(self):
                return "- generic: root"

        return _Locator()

    def screenshot(self, path):
        with open(path, "wb") as f:
            f.write(b"fake-png-bytes")

    def close(self):
        self.closed = True


class FakeBrowser:
    def __init__(self):
        self.page = FakePage()
        self.closed = False

    def new_page(self):
        return self.page

    def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self):
        self.browser = FakeBrowser()

    def launch(self, headless=True):
        return self.browser


class FakePlaywrightContext:
    def __init__(self):
        self.chromium = FakeChromium()
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeSyncPlaywright:
    def __init__(self):
        self.context = FakePlaywrightContext()

    def start(self):
        return self.context

    def __call__(self):
        return self


def test_playwright_adapter_requires_start_url():
    adapter = PlaywrightEnvironmentAdapter()
    with pytest.raises(ValueError, match="start_url"):
        adapter.reset(make_task(metadata={}))


def test_playwright_adapter_dispatches_click_and_type(monkeypatch):
    fake = FakeSyncPlaywright()
    monkeypatch.setattr(playwright_adapter, "sync_playwright", fake)

    adapter = PlaywrightEnvironmentAdapter(headless=True)
    obs = adapter.reset(make_task(metadata={"start_url": "https://example.invalid/start"}))
    assert obs.done is False
    assert obs.accessibility_tree == "- generic: root"
    assert obs.available_elements == [{"id": "#go", "tag": "button", "label": "Go"}]

    result = adapter.execute_action(Action(action="click", target="#go"))
    assert result.success is True
    assert fake.context.chromium.browser.page.clicked == ["#go"]

    result = adapter.execute_action(Action(action="type", target="#name", text="hi"))
    assert result.success is True
    assert fake.context.chromium.browser.page.filled == [("#name", "hi")]


def test_playwright_adapter_finish_marks_done(monkeypatch):
    fake = FakeSyncPlaywright()
    monkeypatch.setattr(playwright_adapter, "sync_playwright", fake)
    adapter = PlaywrightEnvironmentAdapter()
    adapter.reset(make_task(metadata={"start_url": "https://example.invalid/start"}))
    result = adapter.execute_action(Action(action="finish"))
    assert result.observation.done is True


def test_playwright_adapter_unsupported_action_reports_failure_not_crash(monkeypatch):
    fake = FakeSyncPlaywright()
    monkeypatch.setattr(playwright_adapter, "sync_playwright", fake)
    adapter = PlaywrightEnvironmentAdapter()
    adapter.reset(make_task(metadata={"start_url": "https://example.invalid/start"}))
    result = adapter.execute_action(Action(action="bogus_action_type"))
    assert result.success is False
    assert "unsupported action type" in result.error


def test_playwright_adapter_close_stops_everything(monkeypatch):
    fake = FakeSyncPlaywright()
    monkeypatch.setattr(playwright_adapter, "sync_playwright", fake)
    adapter = PlaywrightEnvironmentAdapter()
    adapter.reset(make_task(metadata={"start_url": "https://example.invalid/start"}))
    adapter.close()
    assert fake.context.chromium.browser.page.closed is True
    assert fake.context.chromium.browser.closed is True
    assert fake.context.stopped is True


def test_playwright_adapter_raises_clear_error_if_playwright_not_installed(monkeypatch):
    monkeypatch.setattr(playwright_adapter, "sync_playwright", None)
    adapter = PlaywrightEnvironmentAdapter()
    with pytest.raises(RuntimeError, match="playwright is not installed"):
        adapter.reset(make_task(metadata={"start_url": "https://example.invalid/start"}))
