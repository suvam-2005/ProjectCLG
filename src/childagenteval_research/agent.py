"""The L0 agent controller and the episode loop that wires it to an Environment and a
Guardrail.

Guardrails are intentionally NOT called from inside Agent. `run_episode` applies the
guardrail to the agent's proposed action before execution — Agent itself has no
knowledge that guardrails exist, so plugging in L1/L2/L3 later never requires touching
this class (see guardrails/interface.py).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Callable

from .actions import Action, ActionValidationError, make_recovery_action, parse_action
from .environment.base import ActionResult, Environment, TaskSpec
from .guardrails.interface import Guardrail, GuardrailDecision, GuardrailResult
from .observation import Observation
from .openrouter_client import OpenRouterClient
from .telemetry.schema import TrajectoryRecord
from .telemetry.writer import TrajectoryWriter

PromptBuilder = Callable[[TaskSpec, Observation], list[dict[str, str]]]


@dataclass
class DecisionResult:
    proposed_action: Action
    raw_model_output: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    cost_usd: float
    cumulative_cost_usd: float
    error: str | None = None
    recovery: str | None = None


class Agent:
    def __init__(
        self,
        model_client: OpenRouterClient,
        telemetry_writer: TrajectoryWriter,
        experiment_id: str,
        run_id: str,
        condition: str,
        prompt_builder: PromptBuilder,
        max_output_tokens: int,
        provider: str = "openrouter",
        extra_request_params: dict | None = None,
    ) -> None:
        self.model_client = model_client
        self.telemetry_writer = telemetry_writer
        self.experiment_id = experiment_id
        self.run_id = run_id
        self.condition = condition
        self.provider = provider
        self.prompt_builder = prompt_builder
        self.max_output_tokens = max_output_tokens
        self.extra_request_params = extra_request_params
        self.task: TaskSpec | None = None

    def initialize(self, task: TaskSpec) -> None:
        self.task = task

    def observe(self, environment_state: Observation) -> Observation:
        """L0 hook: pass-through. Exists so a future guardrail/preprocessing layer has
        somewhere to attach without changing the agent's public interface."""
        return environment_state

    def decide(self, observation: Observation) -> DecisionResult:
        assert self.task is not None, "Agent.initialize(task) must be called before decide()"
        messages = self.prompt_builder(self.task, observation)
        result = self.model_client.chat(
            self.task.task_id, messages, max_tokens=self.max_output_tokens, extra=self.extra_request_params
        )
        # A provider can return null content (e.g. the completion budget was entirely
        # consumed by hidden reasoning tokens, leaving nothing visible) — normalize to
        # "" so this is handled as ordinary malformed output, not a crash.
        content = result["content"] or ""

        error: str | None = None
        recovery: str | None = None
        try:
            action = parse_action(content)
        except ActionValidationError as e:
            error = str(e)
            recovery = "applied fixed no-op(wait) recovery action; model was not re-queried"
            action = make_recovery_action(reason=error, raw_model_output=content)

        return DecisionResult(
            proposed_action=action,
            raw_model_output=content,
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            latency_s=result["latency_s"],
            cost_usd=result["cost_usd"],
            cumulative_cost_usd=result["cumulative_cost_usd"],
            error=error,
            recovery=recovery,
        )

    def execute(self, action: Action, environment: Environment) -> ActionResult:
        return environment.execute_action(action)

    def record(
        self,
        step_number: int,
        observation: Observation,
        decision: DecisionResult,
        guardrail_result: GuardrailResult,
        final_action: Action,
        action_result: ActionResult,
        final_score: float | None = None,
    ) -> TrajectoryRecord:
        assert self.task is not None
        record = TrajectoryRecord(
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            task_id=self.task.task_id,
            subtest=self.task.subtest,
            target_age=self.task.target_age,
            model=self.model_client.model,
            provider=self.provider,
            condition=self.condition,
            timestamp=time.time(),
            step_number=step_number,
            observation_metadata=observation.to_dict(),
            action={
                "proposed": decision.proposed_action.to_dict(),
                "guardrail_decision": guardrail_result.decision.value,
                "guardrail_intervention_type": guardrail_result.intervention_type,
                "guardrail_reason": guardrail_result.reason,
                "guardrail_confidence": guardrail_result.confidence,
                "guardrail_metadata": guardrail_result.metadata,
                "final": final_action.to_dict(),
            },
            action_result={
                "success": action_result.success,
                "observation": action_result.observation.to_dict(),
                "error": action_result.error,
            },
            latency_s=decision.latency_s,
            input_tokens=decision.input_tokens,
            output_tokens=decision.output_tokens,
            cost_usd=decision.cost_usd,
            cumulative_cost_usd=decision.cumulative_cost_usd,
            error=decision.error,
            recovery=decision.recovery,
            final_score=final_score,
        )
        self.telemetry_writer.write(record)
        return record

    def terminate(self) -> None:
        """L0 hook: no-op. Reserved for future guardrail/session cleanup."""


def apply_guardrail(proposed: Action, result: GuardrailResult) -> Action:
    """Turns a GuardrailResult into the action that actually gets executed. For L0's
    NoGuardrail this is always a no-op (ALLOW), but the branches below must exist so
    that swapping in L1/L2/L3 later never requires changing this function's caller."""
    if result.decision == GuardrailDecision.ALLOW:
        return proposed
    if result.decision == GuardrailDecision.REJECT:
        return make_recovery_action(
            reason=f"guardrail_reject:{result.reason}",
            raw_model_output=json.dumps(proposed.to_dict()),
        )
    if result.decision == GuardrailDecision.MODIFY:
        assert result.modified_content is not None, "MODIFY must set modified_content"
        try:
            return parse_action(result.modified_content)
        except ActionValidationError as e:
            return make_recovery_action(
                reason=f"guardrail_modify_invalid:{e}",
                raw_model_output=result.modified_content,
            )
    raise ValueError(f"unknown guardrail decision: {result.decision!r}")


def run_episode(
    agent: Agent,
    environment: Environment,
    guardrail: Guardrail,
    task: TaskSpec,
    max_steps: int,
) -> list[TrajectoryRecord]:
    """Drives one task to completion (or max_steps, whichever comes first — a bounded
    episode length, not a retry loop). This is the only place that calls the guardrail;
    Agent and Environment never reference each other's guardrail."""
    agent.initialize(task)
    observation = environment.reset(task)
    records: list[TrajectoryRecord] = []

    for step in range(max_steps):
        observation = agent.observe(observation)
        if observation.done:
            break

        decision = agent.decide(observation)
        guardrail_result = guardrail.evaluate(
            context={
                "task": task,
                "observation": observation,
                "proposed_action": decision.proposed_action,
                "raw_model_output": decision.raw_model_output,
                "decision_error": decision.error,
                "step_number": step,
                "history": list(records),  # records completed so far this episode, oldest first
            }
        )
        final_action = apply_guardrail(decision.proposed_action, guardrail_result)

        action_result = agent.execute(final_action, environment)
        record = agent.record(
            step_number=step,
            observation=observation,
            decision=decision,
            guardrail_result=guardrail_result,
            final_action=final_action,
            action_result=action_result,
        )
        records.append(record)

        observation = action_result.observation
        if final_action.action == "finish" or observation.done:
            break

    agent.terminate()
    environment.close()
    return records
