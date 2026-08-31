import json
from pathlib import Path

import pytest

from childagenteval_research.actions import ActionSource
from childagenteval_research.agent import Agent, apply_guardrail, run_episode
from childagenteval_research.environment.base import TaskSpec
from childagenteval_research.environment.mock_environment import MockEnvironment
from childagenteval_research.guardrails.interface import (
    GuardrailDecision,
    GuardrailResult,
    NoGuardrail,
)
from childagenteval_research.telemetry.writer import TrajectoryWriter


class FakeModelClient:
    """Stands in for OpenRouterClient — returns canned responses in order, never
    touches the network."""

    def __init__(self, contents: list[str]):
        self.model = "qwen/qwen3.5-27b"
        self._contents = list(contents)
        self.call_count = 0

    def chat(self, task_id, messages, max_tokens, extra=None):
        self.call_count += 1
        content = self._contents[min(self.call_count - 1, len(self._contents) - 1)]
        return {
            "request_id": f"fake-{self.call_count}",
            "content": content,
            "input_tokens": 20,
            "output_tokens": 5,
            "latency_s": 0.01,
            "cost_usd": 0.000001,
            "cumulative_cost_usd": 0.000001 * self.call_count,
        }


def make_task(**overrides) -> TaskSpec:
    defaults = dict(task_id="t1", subtest="infra_test", target_age=10, metadata={})
    defaults.update(overrides)
    return TaskSpec(**defaults)


def dummy_prompt_builder(task, observation):
    return [{"role": "user", "content": "irrelevant for fake client"}]


def make_agent(client: FakeModelClient, jsonl_path: Path, condition: str = "L0_none") -> Agent:
    return Agent(
        model_client=client,
        telemetry_writer=TrajectoryWriter(path=jsonl_path),
        experiment_id="test-experiment-id",
        run_id="l0_dev",
        condition=condition,
        prompt_builder=dummy_prompt_builder,
        max_output_tokens=64,
        provider="mock",
    )


# ---- Agent.decide ----

def test_decide_parses_valid_action():
    client = FakeModelClient([json.dumps({"action": "click", "target": "mock_button"})])
    agent = make_agent(client, Path("unused.jsonl"))
    agent.initialize(make_task())
    env = MockEnvironment()
    obs = env.reset(make_task())

    decision = agent.decide(obs)
    assert decision.proposed_action.action == "click"
    assert decision.error is None
    assert client.call_count == 1


def test_decide_applies_recovery_when_content_is_none_not_a_crash():
    # Regression test: a provider can return null content (e.g. the completion budget
    # was entirely consumed by hidden reasoning tokens) — this must not crash
    # json.loads(None), it must be treated as ordinary malformed output.
    client = FakeModelClient([])
    client.chat = lambda task_id, messages, max_tokens, extra=None: {
        "request_id": "fake-1", "content": None, "input_tokens": 20, "output_tokens": 128,
        "latency_s": 0.01, "cost_usd": 0.0001, "cumulative_cost_usd": 0.0001,
    }
    agent = make_agent(client, Path("unused.jsonl"))
    agent.initialize(make_task())
    env = MockEnvironment()
    obs = env.reset(make_task())

    decision = agent.decide(obs)
    assert decision.proposed_action.source == ActionSource.MALFORMED_RECOVERY
    assert decision.raw_model_output == ""


def test_decide_applies_recovery_on_malformed_output_without_requerying_model():
    client = FakeModelClient(["not valid json at all"])
    agent = make_agent(client, Path("unused.jsonl"))
    agent.initialize(make_task())
    env = MockEnvironment()
    obs = env.reset(make_task())

    decision = agent.decide(obs)
    assert decision.proposed_action.source == ActionSource.MALFORMED_RECOVERY
    assert decision.error is not None
    assert decision.recovery is not None
    assert client.call_count == 1  # never re-queried the model


# ---- apply_guardrail ----

def test_apply_guardrail_allow_passes_through():
    from childagenteval_research.actions import Action

    proposed = Action(action="click", target="x")
    result = GuardrailResult(decision=GuardrailDecision.ALLOW)
    assert apply_guardrail(proposed, result) is proposed


def test_apply_guardrail_reject_returns_safe_recovery():
    from childagenteval_research.actions import Action

    proposed = Action(action="click", target="x")
    result = GuardrailResult(decision=GuardrailDecision.REJECT, reason="too risky")
    final = apply_guardrail(proposed, result)
    assert final.action == "wait"
    assert final.source == ActionSource.MALFORMED_RECOVERY
    assert "too risky" in final.metadata["reason"]


def test_apply_guardrail_modify_parses_new_action():
    from childagenteval_research.actions import Action

    proposed = Action(action="click", target="x")
    result = GuardrailResult(
        decision=GuardrailDecision.MODIFY,
        modified_content=json.dumps({"action": "wait"}),
    )
    final = apply_guardrail(proposed, result)
    assert final.action == "wait"


# ---- run_episode (Agent + MockEnvironment + NoGuardrail) ----

def test_run_episode_click_type_finish_writes_trajectory(tmp_path):
    client = FakeModelClient(
        [
            json.dumps({"action": "click", "target": "mock_button"}),
            json.dumps({"action": "type", "target": "mock_input", "text": "hello"}),
            json.dumps({"action": "finish"}),
        ]
    )
    jsonl_path = tmp_path / "t1.jsonl"
    agent = make_agent(client, jsonl_path)
    env = MockEnvironment()
    guardrail = NoGuardrail()
    task = make_task()

    records = run_episode(agent, env, guardrail, task, max_steps=10)

    assert len(records) == 3
    assert records[-1].action["final"]["action"] == "finish"
    assert client.call_count == 3

    persisted = TrajectoryWriter(path=jsonl_path).read_all()
    assert len(persisted) == 3
    assert [r["step_number"] for r in persisted] == [0, 1, 2]


def test_run_episode_never_exceeds_zero_guardrail_intervention_for_l0(tmp_path):
    client = FakeModelClient([json.dumps({"action": "finish"})])
    jsonl_path = tmp_path / "t1.jsonl"
    agent = make_agent(client, jsonl_path)
    env = MockEnvironment()
    guardrail = NoGuardrail()

    records = run_episode(agent, env, guardrail, make_task(), max_steps=5)
    assert len(records) == 1
    assert records[0].action["guardrail_decision"] == "allow"
    assert records[0].action["proposed"] == records[0].action["final"]


def test_run_episode_respects_max_steps_when_agent_never_finishes(tmp_path):
    client = FakeModelClient([json.dumps({"action": "wait"})])
    jsonl_path = tmp_path / "t1.jsonl"
    agent = make_agent(client, jsonl_path)
    env = MockEnvironment()
    guardrail = NoGuardrail()

    records = run_episode(agent, env, guardrail, make_task(), max_steps=4)
    assert len(records) == 4
    assert client.call_count == 4
