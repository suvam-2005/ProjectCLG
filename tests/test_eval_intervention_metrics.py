from childagenteval_research.evaluation.intervention_metrics import (
    InterventionEvent,
    summarize_interventions,
    unnecessary_intervention_rate,
)


def test_summarize_interventions_counts_each_type():
    events = [
        InterventionEvent(step_number=0, intervention_type=None),
        InterventionEvent(step_number=1, intervention_type="reject", reason="too risky", latency_s=0.1),
        InterventionEvent(step_number=2, intervention_type="modify", latency_s=0.2),
        InterventionEvent(step_number=3, intervention_type="reject", was_replan=True, latency_s=0.05),
    ]
    summary = summarize_interventions(events, opportunities=4)
    assert summary.intervention_count == 3
    assert summary.accepted_action_count == 1
    assert summary.rejected_action_count == 2
    assert summary.modified_output_count == 1
    assert summary.replan_count == 1
    assert summary.intervention_rate == 0.75
    assert summary.intervention_latencies_s == [0.1, 0.2, 0.05]


def test_intervention_rate_none_when_no_opportunities():
    summary = summarize_interventions([], opportunities=0)
    assert summary.intervention_rate is None


def test_unnecessary_intervention_rate_requires_explicit_evaluator():
    interventions = [InterventionEvent(step_number=0, intervention_type="reject")]
    assert unnecessary_intervention_rate(interventions, posthoc_evaluator=None) is None
    assert unnecessary_intervention_rate([], posthoc_evaluator=lambda e: True) is None


def test_unnecessary_intervention_rate_uses_evaluator_when_given():
    interventions = [
        InterventionEvent(step_number=0, intervention_type="reject"),
        InterventionEvent(step_number=1, intervention_type="reject"),
    ]
    # pretend a post-hoc evaluator says the first would've been fine, the second not
    evaluator = lambda e: e.step_number == 0
    assert unnecessary_intervention_rate(interventions, evaluator) == 0.5
