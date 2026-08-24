"""Builds the messages sent to the model for a decision step.

IMPORTANT: ChildAgentEval's exact "standard age prompting" wording (the paper's baseline
condition) is not published — see docs/phase0_findings.md. The text loaded here from a
configurable path is OUR OWN placeholder for exercising the harness end-to-end. It must
never be used to produce or claim an OFFICIAL_REPRODUCTION result.
"""
from __future__ import annotations

import json
from pathlib import Path

from .actions import VALID_ACTION_TYPES
from .environment.base import TaskSpec
from .observation import Observation

ACTION_SCHEMA_INSTRUCTIONS = (
    "Respond with exactly one JSON object describing your next action, and nothing "
    f"else — no explanation, no reasoning. The \"action\" field must be one of: "
    f"{sorted(VALID_ACTION_TYPES)}. Include only the fields relevant to that action "
    "(e.g. \"target\" for click; \"target\" and \"text\" for type)."
)


def load_standard_age_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_l0_messages(task: TaskSpec, observation: Observation, standard_age_prompt: str) -> list[dict[str, str]]:
    system = f"{standard_age_prompt}\n\n{ACTION_SCHEMA_INSTRUCTIONS}"
    user = json.dumps(
        {
            "task_id": task.task_id,
            "subtest": task.subtest,
            "target_age": task.target_age,
            "observation": observation.to_dict(),
        }
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
