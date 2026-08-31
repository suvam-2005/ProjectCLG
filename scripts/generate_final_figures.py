"""Generates all 10 required figures from the frozen L0-L3 benchmark's REAL processed
data (data/independent_benchmark/processed/, data/independent_benchmark/statistics/).
No synthetic data, no fabricated error bars — where a legitimate uncertainty interval
exists (n=4 ages, or n=32 tasks) it's computed and shown; where it wouldn't be
legitimate (e.g., a value that is a fixed sum, not a sampled statistic) none is drawn.
"""
from __future__ import annotations

import json
from pathlib import Path

from childagenteval_research.evaluation.reporting import generate_figure_caption
from childagenteval_research.evaluation.figure_spec import FIGURE_PLAN
from childagenteval_research.evaluation.statistics_utils import describe
from childagenteval_research.evaluation.visualization import (
    plot_age_vs_alignment,
    plot_alignment_capability_pareto,
    plot_cost_vs_performance,
    plot_error_categories,
    plot_guardrail_vs_alignment,
    plot_guardrail_vs_capability_retention,
    plot_multi_series_by_age,
    plot_per_category_grouped,
)

PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "independent_benchmark" / "processed"
STATS_DIR = PROJECT_ROOT / "data" / "independent_benchmark" / "statistics"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
CONDITIONS = ["L0", "L1", "L2", "L3"]
AGES = [7, 10, 13, 16]
REFERENCE_QWEN = {7: 0.32, 10: 0.34, 13: 0.29, 16: 0.30}


def load(name: str) -> dict:
    return json.loads((PROCESSED_DIR / name).read_text())


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    capability = load("capability.json")
    alignment_condition = load("alignment_condition_level.json")
    alignment_by_age = load("alignment_by_condition_age.json")
    tradeoff = load("tradeoff.json")
    aggregates = load("aggregates.json")
    per_age = load("per_age.json")
    per_category = load("per_category.json")

    captions = {}

    def save(fig, filename, fig_number, n_used=None):
        path = FIGURES_DIR / filename
        fig.savefig(path, dpi=150, bbox_inches="tight")
        spec = next(s for s in FIGURE_PLAN if s.number == fig_number)
        captions[fig_number] = generate_figure_caption(spec, n_used=n_used)
        print(f"Figure {fig_number} -> {path}")

    # FIGURE 1: Reference Qwen3.5-27B age trajectory
    fig1 = plot_age_vs_alignment(
        AGES, [REFERENCE_QWEN[a] for a in AGES], is_synthetic=False,
        title="Reference paper — reported result (Qwen3.5-27B)",
    )
    fig1.axes[0].set_ylabel("Reference total composite score")
    save(fig1, "figure1_reference_trajectory.png", 1, n_used=4)

    # FIGURE 2: Reference vs our L0
    our_l0_by_age = {a: per_age["L0"][str(a)] / 8 for a in AGES}
    fig2 = plot_multi_series_by_age(
        AGES,
        {"Reference (paper, reported)": [REFERENCE_QWEN[a] for a in AGES],
         "Our L0 (independent benchmark)": [our_l0_by_age[a] for a in AGES]},
        ylabel="Score (NOT the same metric — see caption)",
        is_synthetic=False,
        title="Reference vs Our L0 — contextual comparison only, metrics not equivalent",
    )
    save(fig2, "figure2_reference_vs_l0.png", 2, n_used=4)

    # FIGURE 3 (PRIMARY): L0-L3 cognitive alignment with real error bars (n=4 ages)
    align_ci = []
    for c in CONDITIONS:
        vals = [alignment_by_age[f"{c}_{a}"] for a in AGES]
        stats = describe(vals)
        align_ci.append(stats.stdev / (len(vals) ** 0.5) if stats.stdev is not None else 0)
    fig3 = plot_guardrail_vs_alignment(
        CONDITIONS, [alignment_condition[c] for c in CONDITIONS], is_synthetic=False,
        title="PRIMARY: Independent Cognitive Alignment Score by Condition (error bars = SEM, n=4 ages)",
        yerr=align_ci,
    )
    save(fig3, "figure3_primary_alignment.png", 3, n_used=4)

    # FIGURE 4: L0-L3 task capability with real error bars (n=32 tasks, SEM of binary scores)
    import childagenteval_research.benchmark.task_run_result as _trr  # noqa: F401 (import kept local to avoid unused warnings elsewhere)

    def load_scores(cond):
        rows = [json.loads(l) for l in (PROJECT_ROOT / "data/independent_benchmark/raw" / f"{cond}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        return [r["score"] for r in rows]

    cap_ci = []
    for c in CONDITIONS:
        stats = describe(load_scores(c))
        cap_ci.append(stats.stdev / (32 ** 0.5) if stats.stdev is not None else 0)
    fig4 = plot_guardrail_vs_capability_retention(
        CONDITIONS, [capability[c] for c in CONDITIONS], is_synthetic=False,
        title="Task Capability (accuracy) by Condition (error bars = SEM, n=32 tasks)",
        yerr=cap_ci,
    )
    fig4.axes[0].set_ylabel("Task capability (accuracy)")
    save(fig4, "figure4_capability.png", 4, n_used=32)

    # FIGURE 5: Alignment vs capability retention
    fig5 = plot_alignment_capability_pareto(
        [alignment_condition[c] for c in CONDITIONS],
        [tradeoff[c]["capability_retention_vs_l0"] for c in CONDITIONS],
        CONDITIONS, is_synthetic=False,
        title="Alignment vs Capability Retention (all 4 conditions coincide — see caption)",
    )
    save(fig5, "figure5_alignment_vs_retention.png", 5, n_used=4)

    # FIGURE 6: Per-age L0-L3 comparison
    fig6 = plot_multi_series_by_age(
        AGES, {c: [per_age[c][str(a)] / 8 for a in AGES] for c in CONDITIONS},
        ylabel="Accuracy", is_synthetic=False, title="Per-Age Accuracy, L0 vs L1 vs L2 vs L3",
    )
    save(fig6, "figure6_per_age.png", 6, n_used=8)

    # FIGURE 7: Per-category performance
    categories = sorted(per_category["L0"].keys())
    fig7 = plot_per_category_grouped(
        categories, {c: [per_category[c][cat] for cat in categories] for c in CONDITIONS},
        is_synthetic=False, title="Per-Category Accuracy, L0 vs L1 vs L2 vs L3",
    )
    save(fig7, "figure7_per_category.png", 7, n_used=4)

    # FIGURE 8: Guardrail intervention rate
    fig8 = plot_guardrail_vs_alignment(
        CONDITIONS, [aggregates[c]["intervention_rate"] for c in CONDITIONS], is_synthetic=False,
        title="Guardrail Intervention Rate by Condition",
    )
    fig8.axes[0].set_ylabel("Intervention rate (interventions / total steps)")
    save(fig8, "figure8_intervention_rate.png", 8, n_used=32)

    # FIGURE 9: Errors / recoveries / mean trajectory length
    fig9 = plot_per_category_grouped(
        CONDITIONS,
        {
            "Errors (count)": [aggregates[c]["errors"] for c in CONDITIONS],
            "Recoveries (count)": [aggregates[c]["recoveries"] for c in CONDITIONS],
            "Mean steps/task": [aggregates[c]["mean_steps"] for c in CONDITIONS],
        },
        is_synthetic=False, title="Errors, Recoveries, and Mean Trajectory Length by Condition",
    )
    fig9.axes[0].set_xlabel("Condition")
    fig9.axes[0].set_ylabel("Count / mean steps")
    save(fig9, "figure9_errors_recovery_trajectory.png", 9, n_used=32)

    # FIGURE 10: Token usage and cost (two panels, different scales)
    from matplotlib.figure import Figure

    fig10 = Figure(figsize=(9, 4))
    ax_tok = fig10.add_subplot(121)
    ax_tok.bar(CONDITIONS, [aggregates[c]["total_tokens"] for c in CONDITIONS])
    ax_tok.set_title("Total tokens")
    ax_tok.set_xlabel("Condition")
    ax_tok.set_ylabel("Tokens")
    ax_cost = fig10.add_subplot(122)
    ax_cost.bar(CONDITIONS, [aggregates[c]["cost_usd"] for c in CONDITIONS])
    ax_cost.set_title("Inference cost (USD)")
    ax_cost.set_xlabel("Condition")
    ax_cost.set_ylabel("USD")
    fig10.suptitle("Token Usage and Inference Cost by Condition")
    save(fig10, "figure10_tokens_cost.png", 10, n_used=32)

    (FIGURES_DIR / "captions.json").write_text(json.dumps(captions, indent=2))
    print("\nAll 10 figures generated.")


if __name__ == "__main__":
    main()
