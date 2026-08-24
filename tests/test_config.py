from pathlib import Path

import pytest
import yaml

from childagenteval_research.config import ExperimentConfig, L0Config

CONFIG_PATH = Path(__file__).parent.parent / "configs" / "qwen_baseline.yaml"
L0_CONFIG_PATH = Path(__file__).parent.parent / "configs" / "l0.yaml"


def test_loads_qwen_baseline_config():
    cfg = ExperimentConfig.from_yaml(CONFIG_PATH)
    assert cfg.model == "qwen/qwen3.5-27b"
    assert cfg.temperature == 0
    assert cfg.provider == "openrouter"
    assert cfg.guardrail == "none"
    assert cfg.max_budget_usd == 10.00


def test_cost_state_file_resolves_relative_to_config_dir():
    cfg = ExperimentConfig.from_yaml(CONFIG_PATH)
    assert cfg.cost_state_file.is_absolute()
    assert cfg.cost_state_file.name == "cost_ledger.json"


def test_loads_l0_config():
    cfg = L0Config.from_yaml(L0_CONFIG_PATH)
    assert cfg.model == "qwen/qwen3.5-27b"
    assert cfg.temperature == 0
    assert cfg.guardrail == "none"
    assert cfg.benchmark_adapter == "official_childagenteval"
    assert cfg.environment_adapter == "mock"
    assert cfg.max_budget_usd == 10.00
    assert cfg.soft_budget_usd == 8.00
    assert cfg.trajectory_dir.is_absolute()
    assert cfg.standard_age_prompt_path.exists()


def test_l0_config_rejects_nonzero_guardrail(tmp_path):
    raw = yaml.safe_load(L0_CONFIG_PATH.read_text())
    raw["guardrail"] = "L1_output"
    bad_config = tmp_path / "l0_bad.yaml"
    bad_config.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError, match="guardrail"):
        L0Config.from_yaml(bad_config)
