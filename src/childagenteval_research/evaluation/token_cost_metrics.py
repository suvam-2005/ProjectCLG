"""Token/cost aggregation. Every number here is a sum/derivation of *actual recorded*
usage (TrajectoryRecord.input_tokens/output_tokens/cost_usd, themselves sourced from
OpenRouter's real `usage` field — see openrouter_client.py) — nothing is estimated when
actual usage already exists. `cumulative_project_cost_usd` must be supplied by the
caller from the real CostGuard ledger, never recomputed from a subset of records.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass
class TokenCostMetrics:
    n: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    api_calls: int
    avg_tokens_per_call: float | None
    max_tokens_per_call: int | None
    inference_cost_usd: float
    cost_per_successful_task_usd: float | None
    cumulative_project_cost_usd: float | None


def compute_token_cost_metrics(
    records: Sequence[Mapping[str, Any]],
    *,
    cumulative_project_cost_usd: float | None = None,
) -> TokenCostMetrics:
    n = len(records)
    input_tokens = sum(r.get("input_tokens", 0) for r in records)
    output_tokens = sum(r.get("output_tokens", 0) for r in records)
    total_tokens = input_tokens + output_tokens
    per_call_totals = [r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in records]
    avg_tokens_per_call = (total_tokens / n) if n else None
    max_tokens_per_call = max(per_call_totals) if per_call_totals else None
    inference_cost_usd = sum(r.get("cost_usd", 0.0) for r in records)

    successful_tasks = {
        r["task_id"] for r in records if r.get("final_score") is not None and r["final_score"] > 0
    }
    cost_per_successful_task_usd = (
        inference_cost_usd / len(successful_tasks) if successful_tasks else None
    )

    return TokenCostMetrics(
        n=n,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        api_calls=n,
        avg_tokens_per_call=avg_tokens_per_call,
        max_tokens_per_call=max_tokens_per_call,
        inference_cost_usd=inference_cost_usd,
        cost_per_successful_task_usd=cost_per_successful_task_usd,
        cumulative_project_cost_usd=cumulative_project_cost_usd,
    )
