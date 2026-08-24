"""Thin OpenRouter chat-completions client with deterministic settings and a mandatory
cost-guard pre-check on every call. The API key is read from the environment only."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .cost_guard import CostGuard

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def estimate_prompt_tokens(messages: list[dict[str, str]]) -> int:
    """Conservative (over-)estimate: ~4 chars/token for English text, rounded up.
    Used only for the pre-request budget check; actual billed tokens come from the
    response `usage` field and are what's recorded to the ledger."""
    total_chars = sum(len(m.get("content", "")) for m in messages)
    return max(1, -(-total_chars // 4))


@dataclass
class OpenRouterClient:
    model: str
    temperature: float
    cost_guard: CostGuard
    timeout_s: float = 60.0

    def __post_init__(self) -> None:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set in the environment. Set it before "
                "constructing OpenRouterClient — the key is never read from config files."
            )
        self._api_key = api_key

    def chat(
        self,
        task_id: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt_tokens_estimate = estimate_prompt_tokens(messages)
        self.cost_guard.check_before_request(task_id, prompt_tokens_estimate, max_tokens)

        start = time.monotonic()
        response = httpx.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": max_tokens,
                **(extra or {}),
            },
            timeout=self.timeout_s,
        )
        latency_s = time.monotonic() - start
        response.raise_for_status()
        body = response.json()

        usage = body.get("usage", {})
        input_tokens = usage.get("prompt_tokens", prompt_tokens_estimate)
        output_tokens = usage.get("completion_tokens", 0)

        actual_cost = self.cost_guard.record_actual(
            task_id=task_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            request_id=body.get("id"),
            latency_s=latency_s,
        )

        return {
            "request_id": body.get("id"),
            "content": body["choices"][0]["message"]["content"],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_s": latency_s,
            "cost_usd": actual_cost,
            "cumulative_cost_usd": self.cost_guard.cumulative_cost_usd,
        }
