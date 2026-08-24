"""Fetches live per-token pricing for a model from OpenRouter's public /models endpoint
(no API key required, not a billed inference call)."""
from __future__ import annotations

import httpx

from .cost_guard import ModelPricing

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


def fetch_pricing(model_id: str) -> ModelPricing:
    response = httpx.get(OPENROUTER_MODELS_URL, timeout=30.0)
    response.raise_for_status()
    for entry in response.json()["data"]:
        if entry["id"] == model_id:
            pricing = entry["pricing"]
            return ModelPricing(
                prompt_usd_per_token=float(pricing["prompt"]),
                completion_usd_per_token=float(pricing["completion"]),
            )
    raise ValueError(f"model {model_id!r} not found in OpenRouter /models listing")
