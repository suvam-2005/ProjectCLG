"""Regression coverage for the Phase 5C schema-instruction fix: the pilot found the
model occasionally emitting a bare JSON integer instead of an action object. This is a
task-agnostic interface fix (same instructions for every task/condition), not tuned on
any task's correctness.
"""
from childagenteval_research.prompts import ACTION_SCHEMA_INSTRUCTIONS


def test_action_schema_instructions_forbid_bare_scalars():
    lowered = ACTION_SCHEMA_INSTRUCTIONS.lower()
    assert "json object" in lowered
    assert "bare number" in lowered
    assert "example" in lowered
