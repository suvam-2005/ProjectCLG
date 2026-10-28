"""Runs one condition (L0/L1/L2/L3/L4) of the Independent Interactive Cognitive-Age
Benchmark against real Qwen3.5-27B via OpenRouter + real Chromium via Playwright.

Usage:
    python scripts/run_independent_benchmark.py --condition L0 --pilot
    python scripts/run_independent_benchmark.py --condition L0
    python scripts/run_independent_benchmark.py --condition L1

Cost is checked against BOTH the $8 benchmark-only cap and the $10 whole-project cap
before every request (layered_cost_guard.py) — the pre-existing project ledger is never
reset. Approving spend past the $6.50 benchmark soft-budget requires explicitly calling
CostGuard.approve_continued_spending() (not done automatically by this script).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv

from childagenteval_research.agent import Agent, run_episode
from childagenteval_research.benchmark.layered_cost_guard import LayeredCostGuard
from childagenteval_research.benchmark.scoring import extract_click_targets, score_task
from childagenteval_research.benchmark.task_run_result import TaskRunResult, append_task_run_result
from childagenteval_research.benchmark.task_schema import TaskDefinition, load_all_tasks
from childagenteval_research.cost_guard import CostGuard, CostGuardConfig
from childagenteval_research.environment.base import TaskSpec
from childagenteval_research.environment.playwright_adapter import PlaywrightEnvironmentAdapter
from childagenteval_research.experiment_identity import build_experiment_identity
from childagenteval_research.guardrails.interface import Guardrail, NoGuardrail
from childagenteval_research.guardrails.l1_output import L1OutputGuardrail
from childagenteval_research.guardrails.l2_action import L2ActionGuardrail
from childagenteval_research.guardrails.l3_dynamic import L3DynamicGuardrail
from childagenteval_research.guardrails.l4_dynamic import L4DynamicGuardrail
from childagenteval_research.openrouter_client import OpenRouterClient
from childagenteval_research.pricing import fetch_pricing
from childagenteval_research.prompts import build_l0_messages, load_standard_age_prompt
from childagenteval_research.telemetry.writer import TrajectoryWriter

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "configs" / "independent_benchmark.yaml"
PROJECT_LEDGER_PATH = PROJECT_ROOT / ".state" / "cost_ledger.json"


def benchmark_ledger_path(condition: str, ledger_tag: str | None = None) -> Path:
    """Each condition gets its OWN ledger file — this is what makes running L0-L3 as
    separate parallel processes safe: no two processes ever read-modify-write the same
    file, so there is no lost-update race on the benchmark-only $8 tracking. The
    whole-project ledger (PROJECT_LEDGER_PATH) is still a single shared file; see
    docs/phase5c_pilot_reliability_and_freeze.md for why parallel writers to *that* file
    specifically are not yet safe, and why serial execution is recommended regardless."""
    if ledger_tag:
        # A different model's runs get their own ledger shards (and therefore their own
        # $8 combined-benchmark cap) so they never mix with the Qwen ledgers.
        return PROJECT_ROOT / ".state" / ledger_tag / f"benchmark_cost_ledger_{condition}.json"
    return PROJECT_ROOT / ".state" / f"benchmark_cost_ledger_{condition}.json"


def total_benchmark_spend(ledger_tag: str | None = None) -> float:
    total = 0.0
    for condition in ("L0", "L1", "L2", "L3", "L4"):
        path = benchmark_ledger_path(condition, ledger_tag)
        if path.exists():
            total += json.loads(path.read_text())["cumulative_cost_usd"]
    return total

def build_guardrail(condition: str) -> tuple[Guardrail, str | None]:
    if condition == "L0":
        return NoGuardrail(), None
    if condition == "L1":
        g = L1OutputGuardrail()
        return g, g.VERSION
    if condition == "L2":
        g = L2ActionGuardrail()
        return g, g.VERSION
    if condition == "L3":
        g = L3DynamicGuardrail()
        return g, g.VERSION
    if condition == "L4":
        g = L4DynamicGuardrail()
        return g, g.VERSION
    raise ValueError(f"unknown condition: {condition!r}")


def run_one_task(
    task: TaskDefinition,
    agent: Agent,
    guardrail: Guardrail,
    max_steps: int,
    trajectory_dir: Path,
) -> TaskRunResult:
    page_path = PROJECT_ROOT / "benchmark" / "pages" / f"{task.task_id}.html"
    start_url = page_path.resolve().as_uri()
    task_spec = TaskSpec(task_id=task.task_id, subtest=task.category, target_age=task.target_age, metadata={"start_url": start_url})

    agent.telemetry_writer = TrajectoryWriter(path=trajectory_dir / f"{task.task_id}.jsonl")
    environment = PlaywrightEnvironmentAdapter(headless=True, dom_assisted=True)

    records = run_episode(agent, environment, guardrail, task_spec, max_steps=max_steps)

    dict_records = [r.to_json_dict() for r in records]
    click_targets = extract_click_targets(dict_records)
    stripped_targets = [t.lstrip("#") for t in click_targets]
    score_result = score_task(task, stripped_targets)

    interventions = sum(1 for r in records if r.action.get("guardrail_decision") != "allow")
    errors = sum(1 for r in records if r.error is not None)
    recoveries = sum(1 for r in records if r.recovery is not None)
    input_tokens = sum(r.input_tokens for r in records)
    output_tokens = sum(r.output_tokens for r in records)
    cost_usd = sum(r.cost_usd for r in records)
    latency_s = sum(r.latency_s for r in records)

    return TaskRunResult(
        experiment_id=agent.experiment_id,
        run_id=agent.run_id,
        condition=agent.condition,
        task_id=task.task_id,
        category=task.category,
        target_age=task.target_age,
        model=agent.model_client.model,
        provider=agent.provider,
        temperature=agent.model_client.temperature,
        guardrail_version=getattr(guardrail, "VERSION", None),
        steps=len(records),
        correct=score_result.correct,
        score=score_result.score,
        outcome=score_result.outcome.value,
        interventions=interventions,
        errors=errors,
        recoveries=recoveries,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        cost_usd=cost_usd,
        latency_s=latency_s,
        timestamp=time.time(),
        git_commit="",  # filled in by caller from a single build_experiment_identity() call
        configuration_hash="",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", required=True, choices=["L0", "L1", "L2", "L3", "L4"])
    parser.add_argument("--pilot", action="store_true", help="run only 1 task per category at age 10")
    parser.add_argument("--task-ids", nargs="*", default=None, help="explicit task_id allowlist (overrides --pilot)")
    parser.add_argument("--out-subdir", default=None, help="path under data/ to write raw results to (default: the config's data_subdir, else independent_benchmark; with --pilot, <that>/pilot)")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="experiment config (default: configs/independent_benchmark.yaml, the Qwen run)")
    parser.add_argument("--resume", action="store_true", help="skip tasks already recorded in this condition's results file (after an interrupted run)")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text())
    ledger_tag = config.get("ledger_tag")

    all_tasks = load_all_tasks(PROJECT_ROOT / "benchmark" / "tasks")
    if args.task_ids:
        tasks = [t for t in all_tasks if t.task_id in args.task_ids]
    elif args.pilot:
        tasks = [t for t in all_tasks if t.target_age == 10]
    else:
        tasks = all_tasks

    pricing = fetch_pricing(config["model"])
    project_guard = CostGuard(
        config=CostGuardConfig(
            max_budget_usd=config["budget"]["project_hard_limit_usd"],
            soft_budget_usd=config["budget"]["project_soft_limit_usd"],
            max_tasks=100000, max_api_calls=100000,
            max_output_tokens_per_call=config["budget"]["max_output_tokens_per_call"],
            ledger_path=PROJECT_LEDGER_PATH,
        ),
        pricing=pricing,
    )

    # Each condition writes to its own ledger file (safe to run as separate processes —
    # no shared-file write races), but the $8 cap is a COMBINED cap across all four
    # conditions. So this condition's effective hard/soft limits are shrunk by however
    # much the *other* conditions have already spent, computed once at startup. This is
    # exactly correct for serial execution; for true concurrent execution it has a
    # narrow race window (two processes could both read a stale combined total right
    # before either writes) — which is one of the reasons serial/batched execution is
    # recommended over true parallelism at this stage (see phase5c report).
    this_ledger_path = benchmark_ledger_path(args.condition, ledger_tag)
    this_ledger_path.parent.mkdir(parents=True, exist_ok=True)
    this_existing = json.loads(this_ledger_path.read_text())["cumulative_cost_usd"] if this_ledger_path.exists() else 0.0
    other_conditions_spent = total_benchmark_spend(ledger_tag) - this_existing
    effective_hard_limit = config["budget"]["benchmark_hard_limit_usd"] - other_conditions_spent
    effective_soft_limit = config["budget"]["benchmark_soft_limit_usd"] - other_conditions_spent

    benchmark_guard = CostGuard(
        config=CostGuardConfig(
            max_budget_usd=effective_hard_limit,
            soft_budget_usd=effective_soft_limit,
            max_tasks=100000, max_api_calls=config["budget"]["max_api_calls"],
            max_output_tokens_per_call=config["budget"]["max_output_tokens_per_call"],
            ledger_path=this_ledger_path,
        ),
        pricing=pricing,
    )
    layered_guard = LayeredCostGuard(project_guard=project_guard, benchmark_guard=benchmark_guard)
    client = OpenRouterClient(model=config["model"], temperature=config["temperature"], cost_guard=layered_guard)

    identity = build_experiment_identity(config_path, run_id=config["run_id"])
    standard_age_prompt_path = PROJECT_ROOT / "configs" / "prompts" / "standard_age_prompt.placeholder.txt"
    standard_age_prompt = load_standard_age_prompt(standard_age_prompt_path)

    def prompt_builder(task_spec, observation):
        return build_l0_messages(task_spec, observation, standard_age_prompt)

    data_subdir = config.get("data_subdir", "independent_benchmark")
    out_subdir = args.out_subdir or (f"{data_subdir}/pilot" if args.pilot else data_subdir)
    out_dir = PROJECT_ROOT / "data" / out_subdir
    raw_dir = out_dir / "raw"
    trajectory_dir = raw_dir / "trajectories" / args.condition
    results_path = raw_dir / f"{args.condition}.jsonl"

    if args.resume and results_path.exists():
        done = {json.loads(l)["task_id"] for l in results_path.read_text(encoding="utf-8").splitlines() if l.strip()}
        tasks = [t for t in tasks if t.task_id not in done]
        print(f"--resume: {len(done)} tasks already recorded, {len(tasks)} remaining")

    guardrail, guardrail_version = build_guardrail(args.condition)
    agent = Agent(
        model_client=client,
        telemetry_writer=TrajectoryWriter(path=trajectory_dir / "_unused.jsonl"),  # overwritten per task
        experiment_id=identity.experiment_id,
        run_id=config["run_id"],
        condition=args.condition,
        prompt_builder=prompt_builder,
        max_output_tokens=config["max_output_tokens"],
        provider="openrouter",
        extra_request_params={"response_format": {"type": "json_object"}, "reasoning": {"enabled": False}},
    )

    print(f"Running condition={args.condition} on {len(tasks)} tasks "
          f"(project spend before: ${project_guard.cumulative_cost_usd:.6f}, "
          f"this-condition spend before: ${benchmark_guard.cumulative_cost_usd:.6f}, "
          f"combined benchmark spend before (all conditions): ${total_benchmark_spend(ledger_tag):.6f})")

    global_step_ceiling = config["max_steps_per_task"]
    for i, task in enumerate(tasks):
        max_steps = min(task.maximum_steps, global_step_ceiling)
        result = run_one_task(task, agent, guardrail, max_steps, trajectory_dir)
        result.git_commit = identity.git_commit
        result.configuration_hash = identity.configuration_hash
        append_task_run_result(result, results_path)
        print(
            f"[{i + 1}/{len(tasks)}] {task.task_id} correct={result.correct} steps={result.steps} "
            f"interventions={result.interventions} cost=${result.cost_usd:.6f} "
            f"benchmark_cumulative=${benchmark_guard.cumulative_cost_usd:.6f}",
            flush=True,
        )

    combined_after = total_benchmark_spend(ledger_tag)
    print(
        f"DONE condition={args.condition}. "
        f"this-condition spend now: ${benchmark_guard.cumulative_cost_usd:.6f}; "
        f"combined benchmark spend now (all conditions): ${combined_after:.6f} "
        f"(remaining ${config['budget']['benchmark_hard_limit_usd'] - combined_after:.6f} of the $8 cap); "
        f"project spend now: ${project_guard.cumulative_cost_usd:.6f}"
    )


if __name__ == "__main__":
    main()
