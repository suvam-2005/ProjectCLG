import json
from pathlib import Path

import pytest

from childagenteval_research.cost_guard import (
    BudgetExceededError,
    CostGuard,
    CostGuardConfig,
    ModelPricing,
    SoftBudgetApprovalRequiredError,
)


def make_guard(tmp_path: Path, **overrides) -> CostGuard:
    defaults = dict(
        max_budget_usd=1.00,
        max_tasks=3,
        max_api_calls=5,
        max_output_tokens_per_call=100,
        ledger_path=tmp_path / "ledger.json",
    )
    defaults.update(overrides)
    config = CostGuardConfig(**defaults)
    pricing = ModelPricing(prompt_usd_per_token=0.001, completion_usd_per_token=0.002)
    return CostGuard(config=config, pricing=pricing)


def test_allows_request_within_budget(tmp_path):
    guard = make_guard(tmp_path, max_budget_usd=10.00)
    guard.check_before_request("task1", prompt_tokens=10, max_output_tokens=10)  # should not raise


def test_rejects_request_that_would_exceed_budget(tmp_path):
    guard = make_guard(tmp_path, max_budget_usd=0.01)
    with pytest.raises(BudgetExceededError):
        guard.check_before_request("task1", prompt_tokens=100, max_output_tokens=100)


def test_rejects_beyond_max_api_calls(tmp_path):
    guard = make_guard(tmp_path, max_api_calls=1, max_budget_usd=10.00)
    guard.record_actual("task1", input_tokens=5, output_tokens=5, request_id="r1", latency_s=0.1)
    with pytest.raises(BudgetExceededError):
        guard.check_before_request("task2", prompt_tokens=5, max_output_tokens=5)


def test_rejects_beyond_max_tasks(tmp_path):
    guard = make_guard(tmp_path, max_tasks=1, max_budget_usd=10.00, max_api_calls=10)
    guard.record_actual("task1", input_tokens=5, output_tokens=5, request_id="r1", latency_s=0.1)
    with pytest.raises(BudgetExceededError):
        guard.check_before_request("task2", prompt_tokens=5, max_output_tokens=5)


def test_record_actual_raises_if_cumulative_exceeds_budget(tmp_path):
    guard = make_guard(tmp_path, max_budget_usd=0.02, max_api_calls=10)
    with pytest.raises(BudgetExceededError):
        guard.record_actual("task1", input_tokens=100, output_tokens=100, request_id="r1", latency_s=0.1)


def test_ledger_persists_across_instances(tmp_path):
    ledger_path = tmp_path / "ledger.json"
    guard1 = make_guard(tmp_path, ledger_path=ledger_path, max_budget_usd=10.00)
    guard1.record_actual("task1", input_tokens=10, output_tokens=10, request_id="r1", latency_s=0.1)
    spent = guard1.cumulative_cost_usd
    assert spent > 0

    guard2 = make_guard(tmp_path, ledger_path=ledger_path, max_budget_usd=10.00)
    assert guard2.cumulative_cost_usd == spent

    on_disk = json.loads(ledger_path.read_text())
    assert on_disk["cumulative_cost_usd"] == spent
    assert "task1" in on_disk["tasks_completed"]


def test_soft_budget_blocks_further_requests_until_explicitly_approved(tmp_path):
    guard = make_guard(tmp_path, max_budget_usd=10.00, soft_budget_usd=0.001, max_api_calls=10)
    with pytest.warns(UserWarning, match="soft budget"):
        guard.record_actual("task1", input_tokens=1000, output_tokens=1000, request_id="r1", latency_s=0.1)

    with pytest.raises(SoftBudgetApprovalRequiredError):
        guard.check_before_request("task2", prompt_tokens=1, max_output_tokens=1)

    guard.approve_continued_spending(reason="reviewed, continuing dev testing")
    guard.check_before_request("task2", prompt_tokens=1, max_output_tokens=1)  # no longer raises


def test_never_exceeds_budget_over_many_calls(tmp_path):
    guard = make_guard(tmp_path, max_budget_usd=0.05, max_tasks=1000, max_api_calls=1000)
    accepted = 0
    for i in range(1000):
        try:
            guard.check_before_request(f"task{i}", prompt_tokens=1, max_output_tokens=1)
        except BudgetExceededError:
            break
        guard.record_actual(f"task{i}", input_tokens=1, output_tokens=1, request_id=str(i), latency_s=0.01)
        accepted += 1
    assert guard.cumulative_cost_usd <= 0.05
    assert accepted < 1000  # guard must have stopped it before exhausting the loop
