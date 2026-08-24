"""Loads an experiment config YAML into a typed object. Parameters are never set in code."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ExperimentConfig:
    run_id: str
    model: str
    provider: str
    temperature: float
    max_output_tokens: int
    benchmark_mode: str
    target_age: int
    guardrail: str
    max_budget_usd: float
    soft_budget_usd: float
    max_tasks: int
    max_api_calls: int
    max_output_tokens_per_call: int
    cost_state_file: Path
    dev_validation_test_split: str

    @classmethod
    def from_yaml(cls, path: Path) -> "ExperimentConfig":
        raw = yaml.safe_load(path.read_text())
        limits = raw["limits"]
        return cls(
            run_id=raw["run_id"],
            model=raw["model"],
            provider=raw["provider"],
            temperature=raw["temperature"],
            max_output_tokens=raw["max_output_tokens"],
            benchmark_mode=raw["benchmark_mode"],
            target_age=raw["target_age"],
            guardrail=raw["guardrail"],
            max_budget_usd=limits["max_budget_usd"],
            soft_budget_usd=limits["soft_budget_usd"],
            max_tasks=limits["max_tasks"],
            max_api_calls=limits["max_api_calls"],
            max_output_tokens_per_call=limits["max_output_tokens_per_call"],
            cost_state_file=(path.parent / raw["cost_state_file"]).resolve(),
            dev_validation_test_split=raw["dev_validation_test_split"],
        )


@dataclass
class L0Config:
    run_id: str
    model: str
    temperature: float
    max_output_tokens: int
    benchmark_adapter: str
    environment_adapter: str
    target_age: int
    guardrail: str
    max_budget_usd: float
    soft_budget_usd: float
    max_tasks: int
    max_api_calls: int
    max_output_tokens_per_call: int
    trajectory_dir: Path
    cost_state_file: Path
    headless: bool
    dom_assisted: bool
    screenshots_dir: Path | None
    standard_age_prompt_path: Path

    @classmethod
    def from_yaml(cls, path: Path) -> "L0Config":
        raw = yaml.safe_load(path.read_text())
        if raw["guardrail"] != "none":
            raise ValueError(
                f"L0Config requires guardrail: none (got {raw['guardrail']!r}) — "
                "L1/L2/L3 are not implemented yet; use a different config for those phases"
            )
        budget = raw["budget"]
        logging_cfg = raw["logging"]
        browser = raw["browser_mode"]
        screenshots_dir = browser.get("screenshots_dir")
        return cls(
            run_id=raw["run_id"],
            model=raw["model"],
            temperature=raw["temperature"],
            max_output_tokens=raw["max_output_tokens"],
            benchmark_adapter=raw["benchmark_adapter"],
            environment_adapter=raw["environment"]["adapter"],
            target_age=raw["target_age"],
            guardrail=raw["guardrail"],
            max_budget_usd=budget["max_budget_usd"],
            soft_budget_usd=budget["soft_budget_usd"],
            max_tasks=budget["max_tasks"],
            max_api_calls=budget["max_api_calls"],
            max_output_tokens_per_call=budget["max_output_tokens_per_call"],
            trajectory_dir=(path.parent / logging_cfg["trajectory_dir"]).resolve(),
            cost_state_file=(path.parent / logging_cfg["cost_state_file"]).resolve(),
            headless=browser["headless"],
            dom_assisted=browser["dom_assisted"],
            screenshots_dir=(path.parent / screenshots_dir).resolve() if screenshots_dir else None,
            standard_age_prompt_path=(path.parent / raw["standard_age_prompt_path"]).resolve(),
        )
