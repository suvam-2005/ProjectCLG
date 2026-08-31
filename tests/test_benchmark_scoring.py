from pathlib import Path

from childagenteval_research.benchmark.scoring import (
    TaskOutcome,
    category_scores,
    extract_click_targets,
    mean_task_score,
    score_task,
)
from childagenteval_research.benchmark.task_schema import load_all_tasks

TASKS_DIR = Path(__file__).parent.parent / "benchmark" / "tasks"
TASKS = {t.task_id: t for t in load_all_tasks(TASKS_DIR)}


def test_correct_multiple_choice_scores_1():
    task = TASKS["reasoning_age7_v1"]
    result = score_task(task, [task.success_condition["correct_choice_id"]])
    assert result.correct is True
    assert result.score == 1.0
    assert result.outcome == TaskOutcome.CORRECT


def test_incorrect_multiple_choice_scores_0():
    task = TASKS["reasoning_age7_v1"]
    wrong = next(c["id"] for c in task.choices if c["id"] != task.success_condition["correct_choice_id"])
    result = score_task(task, [wrong])
    assert result.correct is False
    assert result.outcome == TaskOutcome.INCORRECT


def test_no_clicks_is_invalid_action_not_silently_incorrect():
    task = TASKS["reasoning_age7_v1"]
    result = score_task(task, [])
    assert result.outcome == TaskOutcome.INVALID_ACTION
    assert result.correct is False


def test_correct_sequence_click_scores_1():
    task = TASKS["wm_age7_v1"]
    result = score_task(task, list(task.success_condition["expected_target_order"]))
    assert result.correct is True


def test_wrong_order_sequence_click_scores_0():
    task = TASKS["wm_age7_v1"]
    reversed_order = list(reversed(task.success_condition["expected_target_order"]))
    result = score_task(task, reversed_order)
    assert result.correct is False


def test_extra_click_in_sequence_scores_0():
    task = TASKS["wm_age7_v1"]
    with_extra = list(task.success_condition["expected_target_order"]) + ["target_star"]
    result = score_task(task, with_extra)
    assert result.correct is False


def test_extract_click_targets_ignores_non_click_actions():
    records = [
        {"action": {"final": {"action": "click", "target": "#choice_a"}}},
        {"action": {"final": {"action": "finish"}}},
    ]
    assert extract_click_targets(records) == ["#choice_a"]


def test_mean_task_score_empty_is_none():
    assert mean_task_score([]) is None


def test_mean_task_score_averages_binary_scores():
    task = TASKS["reasoning_age7_v1"]
    correct = score_task(task, [task.success_condition["correct_choice_id"]])
    incorrect = score_task(task, ["nope"])
    assert mean_task_score([correct, incorrect]) == 0.5


def test_category_scores_grouped_correctly():
    reasoning_task = TASKS["reasoning_age7_v1"]
    language_task = TASKS["language_age7_v1"]
    results = [
        score_task(reasoning_task, [reasoning_task.success_condition["correct_choice_id"]]),
        score_task(language_task, ["nope"]),
    ]
    scores = category_scores(results, TASKS)
    assert scores["reasoning"] == 1.0
    assert scores["language"] == 0.0
