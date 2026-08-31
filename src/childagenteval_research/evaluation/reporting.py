"""Automated reporting architecture (brief §17): turns real EvaluationResult /
ConditionComparisonResult / FigureSpec data into CSV/JSON/markdown output. Generates
nothing from scratch — every function here is a pure transformation of data the caller
already measured.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .comparisons import ConditionComparisonResult, MetricComparison
from .figure_spec import FigureSpec
from .result_schema import EvaluationResult


def results_to_json(results: list[EvaluationResult], path: Path) -> None:
    path.write_text(json.dumps([r.to_dict() for r in results], indent=2))


def results_to_csv(results: list[EvaluationResult], path: Path) -> None:
    if not results:
        path.write_text("")
        return
    rows = [r.to_dict() for r in results]
    for row in rows:
        for key, value in row.items():
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(value)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _fmt_metric_comparison(mc: MetricComparison) -> str:
    if mc.mean_difference is None:
        return f"n/a (n={mc.a_stats.n}/{mc.b_stats.n})"
    return f"{mc.mean_difference:+.3f} (n={mc.a_stats.n}/{mc.b_stats.n})"


def comparison_table_to_markdown(comparisons: list[ConditionComparisonResult]) -> str:
    header = (
        "| Comparison | Task Performance Δ | Alignment Δ | Intervention Δ | "
        "Trajectory Δ | Tokens Δ | Cost Δ |"
    )
    separator = "|---|---|---|---|---|---|---|"
    rows = [
        f"| {c.condition_a} vs {c.condition_b} "
        f"| {_fmt_metric_comparison(c.task_performance)} "
        f"| {_fmt_metric_comparison(c.alignment)} "
        f"| {_fmt_metric_comparison(c.intervention)} "
        f"| {_fmt_metric_comparison(c.trajectory)} "
        f"| {_fmt_metric_comparison(c.tokens)} "
        f"| {_fmt_metric_comparison(c.cost)} |"
        for c in comparisons
    ]
    return "\n".join([header, separator, *rows])


def generate_figure_caption(spec: FigureSpec, n_used: int | None = None) -> str:
    if not spec.data_currently_exists:
        return (
            f"Figure {spec.number} ({spec.title}): DATA NOT YET AVAILABLE — requires "
            f"{', '.join(spec.required_data)}."
        )
    n_clause = f" (n={n_used})" if n_used is not None else ""
    return (
        f"Figure {spec.number}. {spec.title}. X-axis: {spec.x_axis}. "
        f"Y-axis: {spec.y_axis} ({spec.units}). Grouped {spec.grouping}. "
        f"{spec.statistical_annotations}{n_clause}."
    )
