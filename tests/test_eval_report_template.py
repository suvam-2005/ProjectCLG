import pytest

from childagenteval_research.evaluation.report_template import (
    ExpectedVsActualReport,
    StatementKind,
    TaggedStatement,
)


def test_report_renders_all_sections():
    report = ExpectedVsActualReport(
        title="Qwen3.5-27B Reproduction",
        what_paper_reported=[TaggedStatement(StatementKind.OBSERVATION, "Paper reports total 0.32 at age 7 (Table 2).")],
        what_we_observed=[TaggedStatement(StatementKind.OBSERVATION, "Our run measured 0.30 at age 7 (n=5).")],
        difference=[TaggedStatement(StatementKind.OBSERVATION, "Absolute difference: -0.02.")],
        statistical_evidence=[TaggedStatement(StatementKind.OBSERVATION, "Welch's t=-0.4, p=0.69, n=5 vs reference point.")],
        possible_explanations=[TaggedStatement(StatementKind.HYPOTHESIS, "Prompt wording differs from the paper's unpublished exact text.")],
        limitations=[TaggedStatement(StatementKind.OBSERVATION, "Reference value itself is only medium-confidence.")],
    )
    markdown = report.render_markdown()
    assert "## What the reference paper expected/reported" in markdown
    assert "## Possible explanations" in markdown
    assert "[HYPOTHESIS]" in markdown
    assert "[OBSERVATION]" in markdown


def test_possible_explanations_rejects_bare_observation():
    with pytest.raises(ValueError):
        ExpectedVsActualReport(
            title="x",
            possible_explanations=[TaggedStatement(StatementKind.OBSERVATION, "This is a fact, not an explanation.")],
        )


def test_possible_explanations_accepts_interpretation():
    report = ExpectedVsActualReport(
        title="x",
        possible_explanations=[TaggedStatement(StatementKind.INTERPRETATION, "The gap is consistent with sampling noise.")],
    )
    assert len(report.possible_explanations) == 1


def test_empty_report_renders_placeholder_sections():
    report = ExpectedVsActualReport(title="Empty")
    markdown = report.render_markdown()
    assert "(none yet)" in markdown
