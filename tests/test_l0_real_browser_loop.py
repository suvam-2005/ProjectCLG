"""Phase 2.5, Part A.4 + Part B: the full L0 loop — Observation -> FakeModelClient ->
Action -> Guardrail (NoGuardrail) -> real Chromium -> new Observation -> ... -> finish —
driven against LOCAL_PLAYWRIGHT_SMOKE_TEST. No OpenRouter call is made: FakeModelClient
never imports or touches childagenteval_research.openrouter_client, and every token/cost
field below is asserted to be exactly zero, not fabricated.
"""
import json
from pathlib import Path

from childagenteval_research.agent import Agent, run_episode
from childagenteval_research.environment.base import TaskSpec
from childagenteval_research.environment.playwright_adapter import PlaywrightEnvironmentAdapter
from childagenteval_research.experiment_identity import build_experiment_identity
from childagenteval_research.guardrails.interface import GuardrailDecision, NoGuardrail
from childagenteval_research.telemetry.writer import TrajectoryWriter

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "local_playwright_smoke_test" / "index.html"
START_URL = FIXTURE_PATH.resolve().as_uri()
L0_CONFIG_PATH = Path(__file__).parent.parent / "configs" / "l0.yaml"


class ZeroCostFakeModelClient:
    """No network call, no OpenRouter import. Reports real zeros, not fabricated ones —
    Part B requires input_tokens=0, output_tokens=0, inference_cost=$0 for this run."""

    def __init__(self, contents: list[str]):
        self.model = "none/fake-model-no-inference"
        self._contents = list(contents)
        self.call_count = 0

    def chat(self, task_id, messages, max_tokens, extra=None):
        self.call_count += 1
        content = self._contents[min(self.call_count - 1, len(self._contents) - 1)]
        return {
            "request_id": None,
            "content": content,
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_s": 0.0,
            "cost_usd": 0.0,
            "cumulative_cost_usd": 0.0,
        }


def dummy_prompt_builder(task, observation):
    return [{"role": "user", "content": "unused by ZeroCostFakeModelClient"}]


def test_full_l0_loop_against_real_chromium_makes_zero_openrouter_calls(tmp_path):
    client = ZeroCostFakeModelClient(
        [
            json.dumps({"action": "click", "target": "#start_button"}),
            json.dumps({"action": "type", "target": "#answer_input", "text": "hello smoke test"}),
            json.dumps({"action": "select", "target": "#choice_select", "value": "a"}),
            json.dumps({"action": "click", "target": "#finish_button"}),
            json.dumps({"action": "finish"}),
        ]
    )

    identity = build_experiment_identity(L0_CONFIG_PATH, run_id="l0_dev")
    jsonl_path = tmp_path / "local_playwright_smoke_test.jsonl"
    agent = Agent(
        model_client=client,
        telemetry_writer=TrajectoryWriter(path=jsonl_path),
        experiment_id=identity.experiment_id,
        run_id="l0_dev",
        condition="L0_none",
        prompt_builder=dummy_prompt_builder,
        max_output_tokens=64,
        provider="none",
    )
    environment = PlaywrightEnvironmentAdapter(headless=True, dom_assisted=True)
    guardrail = NoGuardrail()
    task = TaskSpec(
        task_id="local_playwright_smoke_test",
        subtest="infra_smoke_test",
        target_age=0,
        metadata={"start_url": START_URL},
    )

    records = run_episode(agent, environment, guardrail, task, max_steps=10)

    # --- Part A.4: the loop completed via a real browser ---
    assert len(records) == 5
    assert records[-1].action["final"]["action"] == "finish"
    assert client.call_count == 5

    # --- Part B: telemetry completeness and no-fabrication ---
    persisted = TrajectoryWriter(path=jsonl_path).read_all()
    assert len(persisted) == 5
    required_fields = {
        "experiment_id", "run_id", "task_id", "subtest", "target_age", "model",
        "provider", "condition", "step_number", "observation_metadata", "action",
        "action_result", "timestamp", "latency_s", "input_tokens", "output_tokens",
        "cost_usd", "cumulative_cost_usd", "error", "recovery", "final_score",
    }
    for i, rec in enumerate(persisted):
        assert required_fields.issubset(rec.keys())
        assert rec["experiment_id"] == identity.experiment_id
        assert rec["run_id"] == "l0_dev"
        assert rec["condition"] == "L0_none"
        assert rec["step_number"] == i
        assert rec["input_tokens"] == 0
        assert rec["output_tokens"] == 0
        assert rec["cost_usd"] == 0.0
        assert rec["cumulative_cost_usd"] == 0.0
        assert rec["action"]["guardrail_decision"] == GuardrailDecision.ALLOW.value
