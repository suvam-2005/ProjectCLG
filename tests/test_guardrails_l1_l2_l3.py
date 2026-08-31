import json

from childagenteval_research.actions import Action, parse_action
from childagenteval_research.guardrails.interface import GuardrailDecision
from childagenteval_research.guardrails.l1_output import L1OutputGuardrail
from childagenteval_research.guardrails.l2_action import L2ActionGuardrail
from childagenteval_research.guardrails.l3_dynamic import L3DynamicGuardrail
from childagenteval_research.observation import Observation
from childagenteval_research.telemetry.schema import TrajectoryRecord


def make_record(step_number, final_action):
    return TrajectoryRecord(
        experiment_id="e", run_id="r", task_id="t", subtest="s", target_age=10,
        model="m", provider="p", condition="c", timestamp=0.0, step_number=step_number,
        observation_metadata={}, action={"final": final_action}, action_result={},
        latency_s=0.0, input_tokens=0, output_tokens=0, cost_usd=0.0, cumulative_cost_usd=0.0,
    )


# ---- L1 ----

def test_l1_allows_clean_json_output():
    guardrail = L1OutputGuardrail()
    raw = json.dumps({"action": "click", "target": "#a"})
    result = guardrail.evaluate(context={"raw_model_output": raw, "decision_error": None})
    assert result.decision == GuardrailDecision.ALLOW


def test_l1_modifies_json_wrapped_in_extra_text():
    guardrail = L1OutputGuardrail()
    raw = 'Sure, I will click that button now.\n' + json.dumps({"action": "click", "target": "#a"}) + '\nDone!'
    result = guardrail.evaluate(context={"raw_model_output": raw, "decision_error": None})
    assert result.decision == GuardrailDecision.MODIFY
    extracted = parse_action(result.modified_content)
    assert extracted.action == "click" and extracted.target == "#a"
    assert result.reason is not None


def test_l1_rejects_output_with_no_extractable_json():
    guardrail = L1OutputGuardrail()
    result = guardrail.evaluate(context={"raw_model_output": "I think I should click something.", "decision_error": None})
    assert result.decision == GuardrailDecision.REJECT
    assert result.confidence is not None


def test_l1_does_not_double_intervene_when_agent_already_flagged_an_error():
    guardrail = L1OutputGuardrail()
    result = guardrail.evaluate(context={"raw_model_output": "garbage", "decision_error": "already handled by agent"})
    assert result.decision == GuardrailDecision.ALLOW


# ---- L2 ----

def make_observation(available_elements):
    return Observation(available_elements=available_elements, done=False)


def test_l2_rejects_premature_finish_at_step_zero():
    guardrail = L2ActionGuardrail()
    result = guardrail.evaluate(context={
        "proposed_action": Action(action="finish"),
        "observation": make_observation([]),
        "step_number": 0,
    })
    assert result.decision == GuardrailDecision.REJECT
    assert "premature_finish" in result.reason


def test_l2_allows_finish_after_step_zero():
    guardrail = L2ActionGuardrail()
    result = guardrail.evaluate(context={
        "proposed_action": Action(action="finish"),
        "observation": make_observation([]),
        "step_number": 1,
    })
    assert result.decision == GuardrailDecision.ALLOW


def test_l2_rejects_target_not_in_available_elements():
    guardrail = L2ActionGuardrail()
    result = guardrail.evaluate(context={
        "proposed_action": Action(action="click", target="#nonexistent"),
        "observation": make_observation([{"id": "#real_button"}]),
        "step_number": 2,
    })
    assert result.decision == GuardrailDecision.REJECT
    assert "target_not_in_available_elements" in result.reason


def test_l2_allows_valid_click_target():
    guardrail = L2ActionGuardrail()
    result = guardrail.evaluate(context={
        "proposed_action": Action(action="click", target="#real_button"),
        "observation": make_observation([{"id": "#real_button"}]),
        "step_number": 2,
    })
    assert result.decision == GuardrailDecision.ALLOW


# ---- L3 ----

def test_l3_allows_first_step_with_no_history():
    guardrail = L3DynamicGuardrail()
    result = guardrail.evaluate(context={
        "proposed_action": Action(action="click", target="#a"),
        "history": [],
        "step_number": 0,
    })
    assert result.decision == GuardrailDecision.ALLOW


def test_l3_modifies_repeated_action_to_wait():
    guardrail = L3DynamicGuardrail()
    history = [make_record(0, {"action": "click", "target": "#a"})]
    result = guardrail.evaluate(context={
        "proposed_action": Action(action="click", target="#a"),
        "history": history,
        "step_number": 1,
    })
    assert result.decision == GuardrailDecision.MODIFY
    assert parse_action(result.modified_content).action == "wait"
    assert result.metadata["trigger"] == "repeated_action"


def test_l3_does_not_flag_different_consecutive_actions():
    guardrail = L3DynamicGuardrail()
    history = [make_record(0, {"action": "click", "target": "#a"})]
    result = guardrail.evaluate(context={
        "proposed_action": Action(action="click", target="#b"),
        "history": history,
        "step_number": 1,
    })
    assert result.decision == GuardrailDecision.ALLOW


def test_l3_forces_finish_after_excessive_steps():
    guardrail = L3DynamicGuardrail()
    history = [make_record(i, {"action": "wait"}) for i in range(5)]
    result = guardrail.evaluate(context={
        "proposed_action": Action(action="wait"),
        "history": history,
        "step_number": 5,
    })
    assert result.decision == GuardrailDecision.MODIFY
    assert parse_action(result.modified_content).action == "finish"
    assert result.metadata["trigger"] == "excessive_steps"


def test_l3_does_not_force_finish_when_agent_already_finishing():
    guardrail = L3DynamicGuardrail()
    history = [make_record(i, {"action": "wait"}) for i in range(5)]
    result = guardrail.evaluate(context={
        "proposed_action": Action(action="finish"),
        "history": history,
        "step_number": 5,
    })
    assert result.decision == GuardrailDecision.ALLOW
