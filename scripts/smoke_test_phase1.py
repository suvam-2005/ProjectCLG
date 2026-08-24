"""Phase 1: exactly ONE real OpenRouter request against qwen/qwen3.5-27b, to validate
the inference/cost/telemetry pipeline end to end. No benchmark, no Playwright, no loop.

Reads OPENROUTER_API_KEY from the environment (loaded from a local .env if present, via
python-dotenv) — never from config or command-line arguments. Refuses to run if the
resolved model or temperature in the config has drifted from the approved baseline.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from dotenv import load_dotenv

from childagenteval_research.config import ExperimentConfig
from childagenteval_research.cost_guard import CostGuard, CostGuardConfig
from childagenteval_research.experiment_identity import build_experiment_identity
from childagenteval_research.openrouter_client import OpenRouterClient
from childagenteval_research.pricing import fetch_pricing
from childagenteval_research.telemetry.schema import TrajectoryRecord

PROJECT_ROOT = Path(__file__).parent.parent
APPROVED_MODEL = "qwen/qwen3.5-27b"
APPROVED_TEMPERATURE = 0

TASK_ID = "phase1_smoke_test"
PROMPT = 'Reply with exactly this JSON and nothing else: {"status": "ok"}'


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    cfg = ExperimentConfig.from_yaml(PROJECT_ROOT / "configs" / "qwen_baseline.yaml")
    if cfg.model != APPROVED_MODEL:
        raise SystemExit(f"refusing to run: config model {cfg.model!r} != approved {APPROVED_MODEL!r}")
    if cfg.temperature != APPROVED_TEMPERATURE:
        raise SystemExit(f"refusing to run: config temperature {cfg.temperature!r} != approved {APPROVED_TEMPERATURE!r}")

    pricing = fetch_pricing(cfg.model)

    guard_config = CostGuardConfig(
        max_budget_usd=cfg.max_budget_usd,
        soft_budget_usd=cfg.soft_budget_usd,
        max_tasks=cfg.max_tasks,
        max_api_calls=cfg.max_api_calls,
        max_output_tokens_per_call=cfg.max_output_tokens_per_call,
        ledger_path=cfg.cost_state_file,
    )
    guard = CostGuard(config=guard_config, pricing=pricing)
    client = OpenRouterClient(model=cfg.model, temperature=cfg.temperature, cost_guard=guard)
    identity = build_experiment_identity(PROJECT_ROOT / "configs" / "qwen_baseline.yaml", run_id=cfg.run_id)

    messages = [{"role": "user", "content": PROMPT}]
    result = client.chat(
        TASK_ID,
        messages,
        max_tokens=16,
        extra={"response_format": {"type": "json_object"}, "reasoning": {"enabled": False}},
    )

    record = TrajectoryRecord(
        experiment_id=identity.experiment_id,
        run_id=cfg.run_id,
        task_id=TASK_ID,
        subtest="infra_smoke_test",
        target_age=cfg.target_age,
        model=cfg.model,
        provider=cfg.provider,
        condition="L0_none",
        timestamp=time.time(),
        step_number=0,
        observation_metadata={"note": "not a ChildAgentEval task; harness validation only"},
        action={"type": "chat", "prompt": PROMPT},
        action_result={"content": result["content"]},
        latency_s=result["latency_s"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        cost_usd=result["cost_usd"],
        cumulative_cost_usd=result["cumulative_cost_usd"],
    )

    run_dir = PROJECT_ROOT / "runs" / TASK_ID
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "trajectory.json").write_text(json.dumps(record.to_json_dict(), indent=2))

    summary = {
        "model": cfg.model,
        "provider": cfg.provider,
        "request_id": result["request_id"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "total_tokens": result["input_tokens"] + result["output_tokens"],
        "cost_usd_this_request": result["cost_usd"],
        "cumulative_cost_usd": result["cumulative_cost_usd"],
        "latency_s": result["latency_s"],
        "response_content": result["content"],
        "pricing_usd_per_token": {
            "prompt": pricing.prompt_usd_per_token,
            "completion": pricing.completion_usd_per_token,
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
