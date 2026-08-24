import pytest

from childagenteval_research.evaluation.token_cost_metrics import compute_token_cost_metrics


def make_record(task_id, input_tokens, output_tokens, cost_usd, final_score=None):
    return {
        "task_id": task_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "final_score": final_score,
    }


def test_aggregates_real_recorded_usage_not_estimates():
    records = [
        make_record("t1", 10, 5, 0.001, final_score=1.0),
        make_record("t1", 8, 4, 0.0008, final_score=1.0),
        make_record("t2", 20, 10, 0.002, final_score=0.0),
    ]
    metrics = compute_token_cost_metrics(records)
    assert metrics.n == 3
    assert metrics.input_tokens == 38
    assert metrics.output_tokens == 19
    assert metrics.total_tokens == 57
    assert metrics.api_calls == 3
    assert metrics.avg_tokens_per_call == 57 / 3
    assert metrics.max_tokens_per_call == 30
    assert metrics.inference_cost_usd == 0.001 + 0.0008 + 0.002


def test_cost_per_successful_task_only_counts_positive_final_score():
    records = [
        make_record("t1", 10, 5, 0.001, final_score=1.0),
        make_record("t2", 10, 5, 0.001, final_score=0.0),
        make_record("t3", 10, 5, 0.001, final_score=None),
    ]
    metrics = compute_token_cost_metrics(records)
    assert metrics.cost_per_successful_task_usd == pytest.approx(0.003)  # only t1 counts as successful


def test_cumulative_project_cost_is_passed_through_not_recomputed():
    metrics = compute_token_cost_metrics([make_record("t1", 1, 1, 0.0001)], cumulative_project_cost_usd=1.8915e-05)
    assert metrics.cumulative_project_cost_usd == 1.8915e-05


def test_empty_records_do_not_crash():
    metrics = compute_token_cost_metrics([])
    assert metrics.n == 0
    assert metrics.avg_tokens_per_call is None
    assert metrics.max_tokens_per_call is None
    assert metrics.inference_cost_usd == 0
