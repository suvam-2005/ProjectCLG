from pathlib import Path

from childagenteval_research.evaluation.failure_taxonomy import FailureCategory, classify_failure
from childagenteval_research.evaluation.metadata import RunMetadata
from childagenteval_research.evaluation.repeated_runs import RepetitionConfig, aggregate_repeated_runs
from childagenteval_research.evaluation.splits import DatasetSplit, NullSplitProvider

L0_CONFIG_PATH = Path(__file__).parent.parent / "configs" / "l0.yaml"


def test_run_metadata_build_populates_reproducibility_fields():
    metadata = RunMetadata.build(
        model="qwen/qwen3.5-27b", provider="openrouter", temperature=0, max_output_tokens=512,
        config_path=L0_CONFIG_PATH, run_id="l0_dev",
    )
    assert metadata.model == "qwen/qwen3.5-27b"
    assert metadata.benchmark_version is None  # honest: unknown until official access
    assert len(metadata.configuration_hash) == 64
    assert metadata.experiment_id


def test_null_split_provider_never_invents_a_split():
    provider = NullSplitProvider()
    assert provider.get_task_split("any_task") is None
    assert isinstance(DatasetSplit.TEST, DatasetSplit)


def test_classify_failure_returns_none_for_clean_step():
    record = {"error": None, "action_result": {"success": True}, "action": {"guardrail_decision": "allow"}}
    assert classify_failure(record) is None


def test_classify_failure_malformed_output():
    record = {
        "error": "response is not valid JSON",
        "recovery": "applied fixed no-op(wait) recovery action; model was not re-queried",
        "action_result": {"success": True},
        "action": {"guardrail_decision": "allow"},
    }
    assert classify_failure(record) == FailureCategory.MALFORMED_OUTPUT


def test_classify_failure_guardrail_intervention():
    record = {
        "error": None, "recovery": None, "action_result": {"success": True},
        "action": {"guardrail_decision": "reject"},
    }
    assert classify_failure(record) == FailureCategory.GUARDRAIL_INTERVENTION


def test_classify_failure_tool_environment_failure():
    record = {
        "error": None, "recovery": None,
        "action_result": {"success": False, "error": "element not found"},
        "action": {"guardrail_decision": "allow"},
    }
    assert classify_failure(record) == FailureCategory.TOOL_ENVIRONMENT_FAILURE


def test_classify_failure_falls_back_to_uncategorized_not_a_guess():
    record = {
        "error": None, "recovery": None,
        "action_result": {"success": False},
        "action": {"guardrail_decision": "allow"},
    }
    assert classify_failure(record) == FailureCategory.UNCATEGORIZED


def test_repetition_config_and_aggregate_repeated_runs():
    config = RepetitionConfig(repetitions=5, seed=42)
    assert config.repetitions == 5
    result = aggregate_repeated_runs([0.5, 0.6, 0.55, 0.52, 0.58], seed=config.seed)
    assert result.stats.n == 5
    assert result.bootstrap_ci.n == 5
