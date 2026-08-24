import pytest

from childagenteval_research.evaluation.capability import TaskPerformanceResult
from childagenteval_research.evaluation.tradeoff import (
    alignment_gain,
    alignment_per_capability_loss,
    capability_change,
    relative_capability_retention,
)


def test_task_performance_result_defaults_to_unknown():
    result = TaskPerformanceResult(task_id="t1")
    assert result.has_any_score() is False
    result2 = TaskPerformanceResult(task_id="t2", raw_score=3.0)
    assert result2.has_any_score() is True


def test_alignment_gain_and_capability_change_are_raw_differences():
    assert alignment_gain(0.8, 0.5) == pytest.approx(0.3)
    assert capability_change(0.4, 0.6) == pytest.approx(-0.2)


def test_relative_capability_retention_handles_zero_baseline():
    assert relative_capability_retention(5.0, 10.0) == 0.5
    assert relative_capability_retention(5.0, 0.0) is None


def test_alignment_per_capability_loss_only_defined_on_actual_loss():
    assert alignment_per_capability_loss(0.2, -0.1) == 2.0
    assert alignment_per_capability_loss(0.2, 0.0) is None
    assert alignment_per_capability_loss(0.2, 0.1) is None
