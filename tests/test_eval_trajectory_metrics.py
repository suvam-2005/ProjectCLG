from childagenteval_research.evaluation.trajectory_metrics import compute_trajectory_metrics


def make_record(step, action="click", target="btn", success=True, recovery=None, url=None, timestamp=0.0, latency_s=0.1):
    return {
        "step_number": step,
        "action": {"final": {"action": action, "target": target}},
        "action_result": {"success": success},
        "recovery": recovery,
        "observation_metadata": {"page_metadata": {"url": url}} if url else {},
        "timestamp": timestamp,
        "latency_s": latency_s,
    }


def test_basic_counts():
    records = [
        make_record(0, success=True, timestamp=0.0),
        make_record(1, success=False, timestamp=1.0),
        make_record(2, success=True, recovery="applied wait", timestamp=2.0),
    ]
    metrics = compute_trajectory_metrics(records)
    assert metrics.n == 3
    assert metrics.total_steps == 3
    assert metrics.successful_steps == 2
    assert metrics.failed_steps == 1
    assert metrics.recovery_steps == 1
    assert metrics.trajectory_length == 3


def test_repeated_actions_counts_consecutive_identical_actions():
    records = [
        make_record(0, action="click", target="a", timestamp=0.0),
        make_record(1, action="click", target="a", timestamp=1.0),
        make_record(2, action="type", target="b", timestamp=2.0),
    ]
    metrics = compute_trajectory_metrics(records)
    assert metrics.repeated_actions == 1


def test_action_diversity_is_distinct_actions_over_total():
    records = [
        make_record(0, action="click", target="a", timestamp=0.0),
        make_record(1, action="click", target="a", timestamp=1.0),
        make_record(2, action="type", target="b", timestamp=2.0),
        make_record(3, action="finish", target=None, timestamp=3.0),
    ]
    metrics = compute_trajectory_metrics(records)
    assert metrics.action_diversity == 3 / 4


def test_page_revisits_none_when_no_url_data():
    records = [make_record(0, timestamp=0.0), make_record(1, timestamp=1.0)]
    metrics = compute_trajectory_metrics(records)
    assert metrics.page_revisits is None


def test_page_revisits_counted_when_urls_present():
    records = [
        make_record(0, url="https://a", timestamp=0.0),
        make_record(1, url="https://b", timestamp=1.0),
        make_record(2, url="https://a", timestamp=2.0),
    ]
    metrics = compute_trajectory_metrics(records)
    assert metrics.page_revisits == 1


def test_unnecessary_actions_is_always_none_not_invented():
    metrics = compute_trajectory_metrics([make_record(0, timestamp=0.0)])
    assert metrics.unnecessary_actions is None


def test_completion_time_and_latency_aggregation():
    records = [
        make_record(0, timestamp=100.0, latency_s=0.5),
        make_record(1, timestamp=103.0, latency_s=1.5),
    ]
    metrics = compute_trajectory_metrics(records)
    assert metrics.completion_time_s == 3.0
    assert metrics.mean_action_latency_s == 1.0
    assert metrics.mean_observation_to_action_latency_s == 1.0


def test_empty_trajectory_does_not_crash():
    metrics = compute_trajectory_metrics([])
    assert metrics.n == 0
    assert metrics.action_diversity is None
    assert metrics.completion_time_s is None
