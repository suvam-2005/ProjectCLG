"""Hard cost guard for OpenRouter inference calls.

Enforces, before every request: a per-call token cap, a call-count cap, a task-count
cap, and a cumulative USD budget cap. Spend is persisted to a local JSON ledger so the
guard survives process restarts and never silently exceeds the configured budget.
"""
from __future__ import annotations

import json
import time
import warnings
from dataclasses import dataclass, field
from pathlib import Path


class BudgetExceededError(RuntimeError):
    pass


class SoftBudgetApprovalRequiredError(RuntimeError):
    """Raised when cumulative spend has crossed the soft budget and no one has called
    CostGuard.approve_continued_spending() since. Distinct from BudgetExceededError:
    this is a pause for a human decision, not a hard stop."""


@dataclass
class ModelPricing:
    prompt_usd_per_token: float
    completion_usd_per_token: float


@dataclass
class CostGuardConfig:
    max_budget_usd: float
    max_tasks: int
    max_api_calls: int
    max_output_tokens_per_call: int
    ledger_path: Path
    soft_budget_usd: float | None = None


@dataclass
class CostGuard:
    config: CostGuardConfig
    pricing: ModelPricing
    _ledger: dict = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.config.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if self.config.ledger_path.exists():
            self._ledger = json.loads(self.config.ledger_path.read_text())
            self._ledger.setdefault("soft_budget_crossed", False)
            self._ledger.setdefault("soft_budget_approved", False)
            self._ledger.setdefault("approvals", [])
        else:
            self._ledger = {
                "run_id": None,
                "cumulative_cost_usd": 0.0,
                "api_calls_made": 0,
                "tasks_completed": set(),
                "soft_budget_crossed": False,
                "soft_budget_approved": False,
                "approvals": [],
                "history": [],
            }
            self._ledger["tasks_completed"] = []  # JSON has no set type
            self._write()

    def _write(self) -> None:
        self.config.ledger_path.write_text(json.dumps(self._ledger, indent=2, default=list))

    @property
    def cumulative_cost_usd(self) -> float:
        return self._ledger["cumulative_cost_usd"]

    def estimate_max_cost(self, prompt_tokens: int, max_output_tokens: int | None = None) -> float:
        out_cap = max_output_tokens if max_output_tokens is not None else self.config.max_output_tokens_per_call
        out_cap = min(out_cap, self.config.max_output_tokens_per_call)
        return (
            prompt_tokens * self.pricing.prompt_usd_per_token
            + out_cap * self.pricing.completion_usd_per_token
        )

    def check_before_request(self, task_id: str, prompt_tokens: int, max_output_tokens: int | None = None) -> None:
        """Raise BudgetExceededError if this request would breach any configured cap."""
        if self._ledger["api_calls_made"] >= self.config.max_api_calls:
            raise BudgetExceededError(
                f"max_api_calls reached ({self.config.max_api_calls}); refusing new request"
            )

        n_tasks = len(set(self._ledger["tasks_completed"]) | {task_id})
        if n_tasks > self.config.max_tasks:
            raise BudgetExceededError(
                f"max_tasks reached ({self.config.max_tasks}); refusing task {task_id}"
            )

        if self._ledger["soft_budget_crossed"] and not self._ledger["soft_budget_approved"]:
            raise SoftBudgetApprovalRequiredError(
                f"cumulative spend ${self.cumulative_cost_usd:.4f} has crossed the soft "
                f"budget (${self.config.soft_budget_usd:.2f}); call "
                "CostGuard.approve_continued_spending(reason=...) before sending more "
                "requests"
            )

        projected = self.estimate_max_cost(prompt_tokens, max_output_tokens)
        projected_total = self.cumulative_cost_usd + projected
        if projected_total > self.config.max_budget_usd:
            raise BudgetExceededError(
                f"projected spend ${projected_total:.4f} exceeds max_budget_usd "
                f"${self.config.max_budget_usd:.2f} (current cumulative "
                f"${self.cumulative_cost_usd:.4f} + projected ${projected:.4f})"
            )

    def record_actual(
        self,
        task_id: str,
        input_tokens: int,
        output_tokens: int,
        request_id: str | None,
        latency_s: float,
    ) -> float:
        """Record the real cost of a completed request. Returns the actual cost in USD."""
        actual_cost = (
            input_tokens * self.pricing.prompt_usd_per_token
            + output_tokens * self.pricing.completion_usd_per_token
        )
        self._ledger["cumulative_cost_usd"] += actual_cost
        self._ledger["api_calls_made"] += 1
        if task_id not in self._ledger["tasks_completed"]:
            self._ledger["tasks_completed"].append(task_id)
        self._ledger["history"].append(
            {
                "task_id": task_id,
                "request_id": request_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": actual_cost,
                "cumulative_cost_usd": self._ledger["cumulative_cost_usd"],
                "latency_s": latency_s,
                "timestamp": time.time(),
            }
        )
        if (
            self.config.soft_budget_usd is not None
            and not self._ledger["soft_budget_crossed"]
            and self._ledger["cumulative_cost_usd"] >= self.config.soft_budget_usd
        ):
            self._ledger["soft_budget_crossed"] = True
            warnings.warn(
                f"cumulative spend ${self._ledger['cumulative_cost_usd']:.4f} has crossed "
                f"the soft budget ${self.config.soft_budget_usd:.2f} (hard cap "
                f"${self.config.max_budget_usd:.2f}) — inference is still allowed but "
                "should be reviewed",
                stacklevel=2,
            )

        self._write()

        if self._ledger["cumulative_cost_usd"] > self.config.max_budget_usd:
            raise BudgetExceededError(
                f"cumulative spend ${self._ledger['cumulative_cost_usd']:.4f} has exceeded "
                f"max_budget_usd ${self.config.max_budget_usd:.2f} after recording actual cost — "
                "halting immediately"
            )
        return actual_cost

    def approve_continued_spending(self, reason: str) -> None:
        """The explicit, human-initiated approval required to keep spending past the
        soft budget. Never call this automatically from a retry loop or scheduler."""
        self._ledger["soft_budget_approved"] = True
        self._ledger["approvals"].append({"reason": reason, "timestamp": time.time()})
        self._write()
