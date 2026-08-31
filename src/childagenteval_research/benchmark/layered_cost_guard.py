"""Every benchmark API call must clear TWO independent budgets simultaneously: the
benchmark-specific $8 cap (a fresh ledger, starting at $0) and the whole-project $10 cap
(the existing ledger, which must keep its pre-existing cumulative spend). Duck-types as
a CostGuard for OpenRouterClient — check_before_request/record_actual/cumulative_cost_usd.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..cost_guard import CostGuard


@dataclass
class LayeredCostGuard:
    project_guard: CostGuard
    benchmark_guard: CostGuard

    def check_before_request(self, task_id: str, prompt_tokens: int, max_output_tokens: int | None = None) -> None:
        self.project_guard.check_before_request(task_id, prompt_tokens, max_output_tokens)
        self.benchmark_guard.check_before_request(task_id, prompt_tokens, max_output_tokens)

    def record_actual(
        self, task_id: str, input_tokens: int, output_tokens: int, request_id: str | None, latency_s: float,
    ) -> float:
        cost = self.benchmark_guard.record_actual(task_id, input_tokens, output_tokens, request_id, latency_s)
        self.project_guard.record_actual(task_id, input_tokens, output_tokens, request_id, latency_s)
        return cost

    @property
    def cumulative_cost_usd(self) -> float:
        return self.benchmark_guard.cumulative_cost_usd

    @property
    def project_cumulative_cost_usd(self) -> float:
        return self.project_guard.cumulative_cost_usd
