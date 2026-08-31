import json

from childagenteval_research.evaluation.comparisons import ConditionResults, compare_conditions
from childagenteval_research.evaluation.conditions import ResearchCondition
from childagenteval_research.evaluation.reporting import (
    comparison_table_to_markdown,
    results_to_csv,
    results_to_json,
)
from childagenteval_research.evaluation.result_schema import EvaluationResult


def make_result(task_id: str, condition: ResearchCondition, score: float) -> EvaluationResult:
    return EvaluationResult(
        experiment_id="exp1", run_id="run1", condition=condition,
        model="qwen/qwen3.5-27b", provider="openrouter", task_id=task_id, task_score=score,
    )


def test_results_to_json_round_trips(tmp_path):
    results = [make_result("t1", ResearchCondition.R0_ORIGINAL_BASELINE, 0.3)]
    path = tmp_path / "results.json"
    results_to_json(results, path)
    loaded = json.loads(path.read_text())
    assert loaded[0]["task_id"] == "t1"
    assert loaded[0]["condition"] == "R0_original_baseline"


def test_results_to_csv_writes_header_and_rows(tmp_path):
    results = [
        make_result("t1", ResearchCondition.R0_ORIGINAL_BASELINE, 0.3),
        make_result("t2", ResearchCondition.R1_OUTPUT_GUARDRAIL, 0.4),
    ]
    path = tmp_path / "results.csv"
    results_to_csv(results, path)
    lines = path.read_text().strip().split("\n")
    assert len(lines) == 3  # header + 2 rows
    assert "task_id" in lines[0]


def test_results_to_csv_empty_list_writes_empty_file(tmp_path):
    path = tmp_path / "empty.csv"
    results_to_csv([], path)
    assert path.read_text() == ""


def test_comparison_table_to_markdown_includes_both_conditions_and_n():
    r0 = ConditionResults(condition="R0", performance_scores=[0.3, 0.32], alignment_scores=[0.2, 0.25])
    r1 = ConditionResults(condition="R1", performance_scores=[0.28, 0.3], alignment_scores=[0.4, 0.45])
    table = comparison_table_to_markdown([compare_conditions(r0, r1)])
    assert "R0 vs R1" in table
    assert "n=2/2" in table
