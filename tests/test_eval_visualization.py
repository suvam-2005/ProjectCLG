from childagenteval_research.evaluation.visualization import (
    plot_age_vs_alignment,
    plot_age_vs_performance,
    plot_alignment_capability_pareto,
    plot_cognitive_profile_radar,
    plot_cost_vs_performance,
    plot_error_categories,
    plot_guardrail_vs_alignment,
    plot_guardrail_vs_capability_retention,
    plot_intervention_rate_vs_alignment,
    plot_trajectory_length_vs_alignment,
)

SYNTHETIC_AGES = [7, 10, 13, 16]
SYNTHETIC_SCORES = [0.2, 0.4, 0.6, 0.8]
SYNTHETIC_CONDITIONS = ["R0", "R1", "R2", "R3"]


def _assert_labeled_test_data(fig):
    ax = fig.axes[0]
    assert "[TEST DATA]" in ax.get_title()


def test_plot_age_vs_alignment_labels_synthetic_data():
    fig = plot_age_vs_alignment(SYNTHETIC_AGES, SYNTHETIC_SCORES, is_synthetic=True)
    _assert_labeled_test_data(fig)


def test_plot_age_vs_performance_labels_synthetic_data():
    fig = plot_age_vs_performance(SYNTHETIC_AGES, SYNTHETIC_SCORES, is_synthetic=True)
    _assert_labeled_test_data(fig)


def test_plot_guardrail_vs_alignment_labels_synthetic_data():
    fig = plot_guardrail_vs_alignment(SYNTHETIC_CONDITIONS, SYNTHETIC_SCORES, is_synthetic=True)
    _assert_labeled_test_data(fig)


def test_plot_guardrail_vs_capability_retention_labels_synthetic_data():
    fig = plot_guardrail_vs_capability_retention(SYNTHETIC_CONDITIONS, [1.0, 0.9, 0.85, 0.8], is_synthetic=True)
    _assert_labeled_test_data(fig)


def test_plot_alignment_capability_pareto_labels_synthetic_data():
    fig = plot_alignment_capability_pareto(SYNTHETIC_SCORES, [0.9, 0.8, 0.7, 0.6], SYNTHETIC_CONDITIONS, is_synthetic=True)
    _assert_labeled_test_data(fig)


def test_plot_intervention_rate_vs_alignment_labels_synthetic_data():
    fig = plot_intervention_rate_vs_alignment([0.0, 0.1, 0.2, 0.3], SYNTHETIC_SCORES, is_synthetic=True)
    _assert_labeled_test_data(fig)


def test_plot_cost_vs_performance_labels_synthetic_data():
    fig = plot_cost_vs_performance([0.01, 0.02, 0.03, 0.04], SYNTHETIC_SCORES, is_synthetic=True)
    _assert_labeled_test_data(fig)


def test_plot_trajectory_length_vs_alignment_labels_synthetic_data():
    fig = plot_trajectory_length_vs_alignment([5, 6, 7, 8], SYNTHETIC_SCORES, is_synthetic=True)
    _assert_labeled_test_data(fig)


def test_plot_error_categories_labels_synthetic_data():
    fig = plot_error_categories({"malformed_output": 2, "guardrail_intervention": 1}, is_synthetic=True)
    _assert_labeled_test_data(fig)


def test_plot_cognitive_profile_radar_labels_synthetic_data():
    fig = plot_cognitive_profile_radar(
        ["reasoning", "language", "working_memory"], [0.5, 0.6, 0.4], [0.3, 0.5, 0.2], is_synthetic=True,
    )
    _assert_labeled_test_data(fig)


def test_non_synthetic_plot_does_not_get_test_data_label():
    fig = plot_age_vs_alignment(SYNTHETIC_AGES, SYNTHETIC_SCORES, is_synthetic=False, title="Real Result")
    assert "[TEST DATA]" not in fig.axes[0].get_title()
    assert fig.axes[0].get_title() == "Real Result"
