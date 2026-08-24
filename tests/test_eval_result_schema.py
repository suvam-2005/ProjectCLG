from childagenteval_research.evaluation.conditions import ResearchCondition
from childagenteval_research.evaluation.profiles import ObservedProfile, ProfileValue, ProfileValueKind, TargetProfile
from childagenteval_research.evaluation.result_schema import EvaluationResult


def test_minimal_result_allows_all_optional_fields_to_be_none():
    result = EvaluationResult(
        experiment_id="exp1", run_id="run1", condition=ResearchCondition.R0_ORIGINAL_BASELINE,
        model="qwen/qwen3.5-27b", provider="openrouter", task_id="t1",
    )
    d = result.to_dict()
    assert d["condition"] == "R0_original_baseline"
    assert d["task_score"] is None
    assert d["target_profile"] is None


def test_result_with_profiles_serializes_enums_to_plain_values():
    target = TargetProfile(values={"reasoning": ProfileValue(kind=ProfileValueKind.NORMALIZED_SCORE, normalized_score=0.5)})
    observed = ObservedProfile(values={"reasoning": ProfileValue(kind=ProfileValueKind.NORMALIZED_SCORE, normalized_score=0.4)})
    result = EvaluationResult(
        experiment_id="exp1", run_id="run1", condition=ResearchCondition.R1_OUTPUT_GUARDRAIL,
        model="qwen/qwen3.5-27b", provider="openrouter", task_id="t1",
        target_profile=target, observed_profile=observed,
    )
    d = result.to_dict()
    assert d["condition"] == "R1_output_guardrail"
    assert d["target_profile"]["values"]["reasoning"]["kind"] == "normalized_score"
    assert d["target_profile"]["values"]["reasoning"]["normalized_score"] == 0.5


def test_to_dict_is_json_serializable():
    import json

    result = EvaluationResult(
        experiment_id="exp1", run_id="run1", condition=ResearchCondition.R0_ORIGINAL_BASELINE,
        model="qwen/qwen3.5-27b", provider="openrouter", task_id="t1",
    )
    json.dumps(result.to_dict())  # must not raise
