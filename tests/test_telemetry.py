from childagenteval_research.guardrails.interface import GuardrailDecision, NoGuardrail
from childagenteval_research.telemetry.schema import TrajectoryRecord


def test_trajectory_record_round_trips_to_json_dict():
    record = TrajectoryRecord(
        experiment_id="test-experiment-id",
        run_id="l0_dev",
        task_id="smoke_1",
        subtest="smoke_test",
        target_age=10,
        model="qwen/qwen3.5-27b",
        provider="openrouter",
        condition="L0_none",
        timestamp=1234.5,
        step_number=0,
        observation_metadata={"note": "harness smoke test"},
        action={"type": "chat"},
        action_result={"content": '{"status": "ok"}'},
        latency_s=0.42,
        input_tokens=10,
        output_tokens=5,
        cost_usd=0.0001,
        cumulative_cost_usd=0.0001,
    )
    d = record.to_json_dict()
    assert d["task_id"] == "smoke_1"
    assert d["final_score"] is None
    assert "api_key" not in d
    assert "OPENROUTER_API_KEY" not in str(d)


def test_no_guardrail_always_allows_unmodified():
    guardrail = NoGuardrail()
    result = guardrail.evaluate(context={"anything": "goes"})
    assert result.decision == GuardrailDecision.ALLOW
    assert result.modified_content is None
    assert result.intervention_type is None
