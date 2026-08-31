"""The paper's eventual publication table plan (brief §11) as data. No unavailable
value is ever populated — a table's `populated` flag stays False until every cell it
needs actually exists.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TableSpec:
    number: int
    title: str
    columns: tuple[str, ...]
    required_data: tuple[str, ...]
    populated: bool


TABLE_PLAN: tuple[TableSpec, ...] = (
    TableSpec(
        number=1, title="Models and configurations",
        columns=("model", "provider", "temperature", "max_output_tokens", "modality"),
        required_data=("configs/*.yaml", "OpenRouter /models metadata"),
        populated=True,  # this much we do have, for Qwen3.5-27B, right now
    ),
    TableSpec(
        number=2, title="Reference methodology vs our reproduction",
        columns=("component", "reference_paper", "our_setup", "status", "evidence"),
        required_data=("docs/reproduction_specification.md",),
        populated=True,
    ),
    TableSpec(
        number=3, title="Reference results",
        columns=("metric", "model", "condition", "age", "subtest", "value", "confidence", "source"),
        required_data=("reference/reference_results.json",),
        populated=True,  # populated, but most rows are low-confidence — see the file itself
    ),
    TableSpec(
        number=4, title="Our independent-benchmark results (L0-L3)",
        columns=("condition", "n", "mean_accuracy", "alignment"),
        required_data=("data/independent_benchmark/processed/capability.json", "alignment_condition_level.json"),
        populated=True,
    ),
    TableSpec(
        number=5, title="L0-L3 comparison",
        columns=("comparison", "task_performance_diff", "alignment_diff", "intervention_diff", "trajectory_diff", "token_diff", "cost_diff"),
        required_data=("data/independent_benchmark/statistics/comparisons_vs_l0.json",),
        populated=True,
    ),
    TableSpec(
        number=6, title="Statistical significance / effect sizes",
        columns=("comparison", "n1", "n2", "t_statistic", "p_value", "corrected_p_value", "cohens_d"),
        required_data=("data/independent_benchmark/statistics/comparisons_vs_l0.json",),
        populated=True,
    ),
    TableSpec(
        number=7, title="Failure analysis",
        columns=("failure_category", "count", "rate", "condition"),
        required_data=("failure_taxonomy.classify_failure() applied to real trajectories",),
        populated=False,  # not computed this phase — errors/recoveries reported at the aggregate level (table 8) instead
    ),
    TableSpec(
        number=8, title="Token/cost analysis",
        columns=("condition", "input_tokens", "output_tokens", "api_calls", "cost_usd", "cost_per_successful_task"),
        required_data=("data/independent_benchmark/processed/aggregates.json",),
        populated=True,
    ),
    TableSpec(
        number=9, title="Ablation results",
        columns=("ablation_variant", "alignment_score", "task_performance", "delta_vs_full"),
        required_data=("L3 ablation runs — not part of this phase's scope",),
        populated=False,
    ),
)
