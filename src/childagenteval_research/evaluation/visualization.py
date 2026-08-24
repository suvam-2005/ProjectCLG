"""Plotting utilities only — no data is generated here. Every function accepts
`is_synthetic: bool`; when True the title is forced to carry a "[TEST DATA]" suffix so a
mock plot can never be mistaken for a real result, regardless of what the caller titled
it. Uses the non-interactive Agg backend (no display needed, safe in test/CI contexts).
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
from matplotlib.figure import Figure  # noqa: E402


def _label(title: str, is_synthetic: bool) -> str:
    return f"{title} [TEST DATA]" if is_synthetic else title


def _line_or_scatter(x, y, xlabel: str, ylabel: str, title: str, is_synthetic: bool, kind: str = "line") -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    (ax.plot if kind == "line" else ax.scatter)(x, y, marker="o")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(_label(title, is_synthetic))
    return fig


def _bar(labels, values, xlabel: str, ylabel: str, title: str, is_synthetic: bool) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.bar([str(l) for l in labels], values)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(_label(title, is_synthetic))
    return fig


def plot_age_vs_alignment(ages, alignment_scores, *, is_synthetic: bool, title: str = "Age vs Cognitive Alignment") -> Figure:
    return _line_or_scatter(ages, alignment_scores, "Target age", "Alignment score", title, is_synthetic)


def plot_age_vs_performance(ages, performance_scores, *, is_synthetic: bool, title: str = "Age vs Task Performance") -> Figure:
    return _line_or_scatter(ages, performance_scores, "Target age", "Task performance", title, is_synthetic)


def plot_guardrail_vs_alignment(conditions, alignment_scores, *, is_synthetic: bool, title: str = "Guardrail Level vs Alignment") -> Figure:
    return _bar(conditions, alignment_scores, "Condition", "Alignment score", title, is_synthetic)


def plot_guardrail_vs_capability_retention(conditions, retention_scores, *, is_synthetic: bool, title: str = "Guardrail Level vs Capability Retention") -> Figure:
    return _bar(conditions, retention_scores, "Condition", "Capability retention", title, is_synthetic)


def plot_alignment_capability_pareto(alignment_scores, capability_scores, labels, *, is_synthetic: bool, title: str = "Alignment-Capability Pareto Frontier") -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.scatter(capability_scores, alignment_scores)
    for x, y, label in zip(capability_scores, alignment_scores, labels):
        ax.annotate(str(label), (x, y))
    ax.set_xlabel("Task capability")
    ax.set_ylabel("Cognitive alignment")
    ax.set_title(_label(title, is_synthetic))
    return fig


def plot_intervention_rate_vs_alignment(intervention_rates, alignment_scores, *, is_synthetic: bool, title: str = "Intervention Rate vs Alignment") -> Figure:
    return _line_or_scatter(intervention_rates, alignment_scores, "Intervention rate", "Alignment score", title, is_synthetic, kind="scatter")


def plot_cost_vs_performance(costs_usd, performance_scores, *, is_synthetic: bool, title: str = "Cost vs Performance") -> Figure:
    return _line_or_scatter(costs_usd, performance_scores, "Cost (USD)", "Task performance", title, is_synthetic, kind="scatter")


def plot_trajectory_length_vs_alignment(trajectory_lengths, alignment_scores, *, is_synthetic: bool, title: str = "Trajectory Length vs Alignment") -> Figure:
    return _line_or_scatter(trajectory_lengths, alignment_scores, "Trajectory length (steps)", "Alignment score", title, is_synthetic, kind="scatter")


def plot_error_categories(category_counts: dict[str, int], *, is_synthetic: bool, title: str = "Model Error Categories") -> Figure:
    return _bar(list(category_counts.keys()), list(category_counts.values()), "Failure category", "Count", title, is_synthetic)


def plot_cognitive_profile_radar(dimension_names, target_values, observed_values, *, is_synthetic: bool, title: str = "Per-Dimension Cognitive Profile") -> Figure:
    import math

    n = len(dimension_names)
    angles = [2 * math.pi * i / n for i in range(n)] + [0.0]
    fig = Figure(figsize=(5, 5))
    ax = fig.add_subplot(111, projection="polar")
    ax.plot(angles, list(target_values) + [target_values[0]], label="Target")
    ax.plot(angles, list(observed_values) + [observed_values[0]], label="Observed")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dimension_names)
    ax.set_title(_label(title, is_synthetic))
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    return fig
