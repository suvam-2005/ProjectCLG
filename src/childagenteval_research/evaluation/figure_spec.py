"""The paper's eventual figure plan (brief §10, updated in Phase 5C for the actual
Independent Interactive Cognitive-Age Benchmark run, L0-L3). No figure is ever rendered
from this module with fake values — `visualization.py` renders real data only, and
forces a [TEST DATA] label whenever synthetic data is used in a test.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FigureSpec:
    number: int
    title: str
    x_axis: str
    y_axis: str
    units: str
    grouping: str
    statistical_annotations: str
    required_data: tuple[str, ...]
    data_currently_exists: bool


FIGURE_PLAN: tuple[FigureSpec, ...] = (
    FigureSpec(
        number=1, title="Reference paper's reported age trajectory",
        x_axis="Target age (7, 10, 13, 16)", y_axis="Reference total composite score",
        units="normalized score, paper's own scale (medium confidence — see reference/README.md)",
        grouping="Qwen3.5-27B baseline only",
        statistical_annotations="none — the paper itself reports no CIs/significance tests (see docs/phase4_reproduction_specification.md)",
        required_data=("reference/reference_results.json",),
        data_currently_exists=True,
    ),
    FigureSpec(
        number=2, title="Reference vs our L0 (contextual comparison only)",
        x_axis="Target age (7, 10, 13, 16)", y_axis="Score (two different metrics, NOT equivalent)",
        units="reference: paper's composite score; ours: independent-benchmark binary accuracy",
        grouping="reference (paper) vs our L0 (independent benchmark)",
        statistical_annotations="none — different scoring systems, not statistically comparable",
        required_data=("reference/reference_results.json", "data/independent_benchmark/raw/L0.jsonl"),
        data_currently_exists=True,
    ),
    FigureSpec(
        number=3, title="L0 vs L1 vs L2 vs L3 cognitive alignment (PRIMARY)",
        x_axis="Condition (L0-L3)", y_axis="Independent cognitive alignment score",
        units="alignment score [0,1], independent_alignment.py formula",
        grouping="by condition, mean across 4 ages",
        statistical_annotations="error bars = SEM across n=4 ages",
        required_data=("data/independent_benchmark/processed/alignment_condition_level.json",),
        data_currently_exists=True,
    ),
    FigureSpec(
        number=4, title="L0 vs L1 vs L2 vs L3 task capability",
        x_axis="Condition (L0-L3)", y_axis="Task capability (accuracy)",
        units="fraction correct [0,1], 32 tasks",
        grouping="by condition",
        statistical_annotations="error bars = SEM across n=32 tasks",
        required_data=("data/independent_benchmark/processed/capability.json",),
        data_currently_exists=True,
    ),
    FigureSpec(
        number=5, title="Alignment vs capability retention",
        x_axis="Task capability retention relative to L0", y_axis="Cognitive alignment score",
        units="ratio (retention), alignment score [0,1]",
        grouping="one point per condition (L0-L3)",
        statistical_annotations="none (Pareto-style scatter) — see caption if points coincide",
        required_data=("data/independent_benchmark/processed/tradeoff.json",),
        data_currently_exists=True,
    ),
    FigureSpec(
        number=6, title="Per-age L0-L3 comparison",
        x_axis="Target age", y_axis="Accuracy",
        units="fraction correct [0,1], n=8 tasks per age per condition",
        grouping="one line per condition",
        statistical_annotations="per-cell n always shown (n=8)",
        required_data=("data/independent_benchmark/processed/per_age.json",),
        data_currently_exists=True,
    ),
    FigureSpec(
        number=7, title="Per-category performance",
        x_axis="Category (8 independent benchmark dimensions)", y_axis="Accuracy",
        units="fraction correct [0,1], n=4 tasks per category per condition",
        grouping="one bar series per condition",
        statistical_annotations="per-cell n always shown (n=4)",
        required_data=("data/independent_benchmark/processed/per_category.json",),
        data_currently_exists=True,
    ),
    FigureSpec(
        number=8, title="Guardrail intervention rate",
        x_axis="Condition (L0-L3)", y_axis="Intervention rate",
        units="interventions / total steps [0,1]",
        grouping="by condition",
        statistical_annotations="rate over n=32 tasks' full step counts per condition",
        required_data=("data/independent_benchmark/processed/aggregates.json",),
        data_currently_exists=True,
    ),
    FigureSpec(
        number=9, title="Errors / recovery / trajectory length",
        x_axis="Condition (L0-L3)", y_axis="Count (errors, recoveries) / mean steps",
        units="count; mean steps per task",
        grouping="by condition, three series",
        statistical_annotations="n=32 tasks per condition",
        required_data=("data/independent_benchmark/processed/aggregates.json",),
        data_currently_exists=True,
    ),
    FigureSpec(
        number=10, title="Inference cost and token consumption",
        x_axis="Condition (L0-L3)", y_axis="Cost (USD) and total tokens (two panels)",
        units="USD; tokens",
        grouping="by condition",
        statistical_annotations="none (cost/tokens are direct sums of actual recorded usage, not sampled statistics)",
        required_data=("data/independent_benchmark/processed/aggregates.json",),
        data_currently_exists=True,
    ),
)
