import json
from pathlib import Path

import httpx
import pytest

from childagenteval_research.cost_guard import BudgetExceededError, CostGuard, CostGuardConfig, ModelPricing
from childagenteval_research.openrouter_client import OpenRouterClient, estimate_prompt_tokens


def make_guard(tmp_path: Path, **overrides) -> CostGuard:
    defaults = dict(
        max_budget_usd=10.00,
        max_tasks=10,
        max_api_calls=10,
        max_output_tokens_per_call=50,
        ledger_path=tmp_path / "ledger.json",
    )
    defaults.update(overrides)
    config = CostGuardConfig(**defaults)
    pricing = ModelPricing(prompt_usd_per_token=0.000000195, completion_usd_per_token=0.00000156)
    return CostGuard(config=config, pricing=pricing)


def fake_response(*, status_code=200, input_tokens=10, output_tokens=5, content='{"status": "ok"}'):
    body = {
        "id": "gen-fake-123",
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": input_tokens, "completion_tokens": output_tokens},
    }
    return httpx.Response(status_code, json=body, request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"))


def test_missing_api_key_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    guard = make_guard(tmp_path)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        OpenRouterClient(model="qwen/qwen3.5-27b", temperature=0, cost_guard=guard)


def test_successful_call_records_actual_cost_and_returns_structured_result(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-does-not-matter")
    guard = make_guard(tmp_path)
    client = OpenRouterClient(model="qwen/qwen3.5-27b", temperature=0, cost_guard=guard)

    monkeypatch.setattr(httpx, "post", lambda *a, **kw: fake_response())

    result = client.chat("smoke_test_1", [{"role": "user", "content": "reply with status ok"}], max_tokens=16)

    assert result["content"] == '{"status": "ok"}'
    assert result["input_tokens"] == 10
    assert result["output_tokens"] == 5
    assert result["request_id"] == "gen-fake-123"
    assert guard.cumulative_cost_usd > 0
    assert "sk-test-does-not-matter" not in json.dumps(result)


def test_failed_request_does_not_record_cost(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-does-not-matter")
    guard = make_guard(tmp_path)
    client = OpenRouterClient(model="qwen/qwen3.5-27b", temperature=0, cost_guard=guard)

    monkeypatch.setattr(httpx, "post", lambda *a, **kw: fake_response(status_code=500))

    with pytest.raises(httpx.HTTPStatusError):
        client.chat("smoke_test_1", [{"role": "user", "content": "hi"}], max_tokens=16)

    assert guard.cumulative_cost_usd == 0
    assert guard._ledger["api_calls_made"] == 0


def test_budget_guard_blocks_call_before_any_network_request(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-does-not-matter")
    guard = make_guard(tmp_path, max_budget_usd=0.0000001)
    client = OpenRouterClient(model="qwen/qwen3.5-27b", temperature=0, cost_guard=guard)

    called = {"n": 0}

    def fake_post(*a, **kw):
        called["n"] += 1
        return fake_response()

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(BudgetExceededError):
        client.chat("smoke_test_1", [{"role": "user", "content": "x" * 1000}], max_tokens=16)

    assert called["n"] == 0  # network must never be hit once the guard rejects


def test_api_key_never_written_to_ledger_file(tmp_path, monkeypatch):
    secret = "sk-super-secret-token-12345"
    monkeypatch.setenv("OPENROUTER_API_KEY", secret)
    ledger_path = tmp_path / "ledger.json"
    guard = make_guard(tmp_path, ledger_path=ledger_path)
    client = OpenRouterClient(model="qwen/qwen3.5-27b", temperature=0, cost_guard=guard)

    monkeypatch.setattr(httpx, "post", lambda *a, **kw: fake_response())
    client.chat("smoke_test_1", [{"role": "user", "content": "hi"}], max_tokens=16)

    assert secret not in ledger_path.read_text()


def test_estimate_prompt_tokens_is_a_conservative_upper_bound():
    messages = [{"role": "user", "content": "a" * 40}]
    assert estimate_prompt_tokens(messages) == 10
    assert estimate_prompt_tokens([{"role": "user", "content": ""}]) == 1
