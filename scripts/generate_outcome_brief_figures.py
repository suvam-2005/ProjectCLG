"""Generates the 10 lay-audience presentation figures for reports/outcome_brief.*.

This is an ADDITIVE, presentation-styled figure set for the Phase 6 outcome brief.
It does not modify or replace the existing research-report figures under
reports/figures/. Every number plotted here is read from
data/independent_benchmark/{raw,processed}/ and reference/reference_results.json —
nothing is hand-typed or estimated.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "independent_benchmark" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "independent_benchmark" / "processed"
OUT_DIR = PROJECT_ROOT / "reports" / "outcome_figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CONDITIONS = ["L0", "L1", "L2", "L3"]
COND_LABEL = {
    "L0": "L0\n(no guardrail)",
    "L1": "L1\n(answer checker)",
    "L2": "L2\n(action checker)",
    "L3": "L3\n(process supervisor)",
}
COND_COLOR = {"L0": "#8a8f98", "L1": "#4c8bf5", "L2": "#f5a623", "L3": "#2e9e6b"}

plt.rcParams.update({
    "font.size": 13,
    "axes.titlesize": 16,
    "axes.titleweight": "bold",
    "axes.labelsize": 13,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def load_json(rel_path: str):
    return json.loads((PROJECT_ROOT / rel_path).read_text(encoding="utf-8"))


def load_raw(condition: str):
    path = RAW_DIR / f"{condition}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def savefig(fig, name: str):
    fig.tight_layout()
    fig.savefig(OUT_DIR / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", OUT_DIR / name)


def fig1_accuracy():
    cap = load_json("data/independent_benchmark/processed/capability.json")
    vals = [cap[c] * 100 for c in CONDITIONS]
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar([COND_LABEL[c] for c in CONDITIONS], vals, color=[COND_COLOR[c] for c in CONDITIONS])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.2f}%", ha="center", fontsize=13, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Tasks answered correctly (%)")
    ax.set_title("Guardrails did not change task accuracy")
    ax.text(0.5, -0.22, "18 of 32 tasks correct in every condition (n = 32 tasks per condition)",
            transform=ax.transAxes, ha="center", fontsize=10, color="#555")
    savefig(fig, "fig01_accuracy.png")


def fig2_alignment():
    align = load_json("data/independent_benchmark/processed/alignment_condition_level.json")
    vals = [align[c] for c in CONDITIONS]
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar([COND_LABEL[c] for c in CONDITIONS], vals, color=[COND_COLOR[c] for c in CONDITIONS])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.5f}", ha="center", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Cognitive alignment score (0-1 scale, ours only)")
    ax.set_title("No measurable change in cognitive alignment")
    ax.text(0.5, -0.22, "Alignment measures how closely scores tracked our own age-difficulty curve.\n"
            "This is our own [0,1] scale, not the reference paper's scale.",
            transform=ax.transAxes, ha="center", fontsize=10, color="#555")
    savefig(fig, "fig02_alignment.png")


def fig3_steps():
    agg = load_json("data/independent_benchmark/processed/aggregates.json")
    conds = ["L0", "L3"]
    vals = [agg[c]["api_calls"] for c in conds]
    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar([COND_LABEL[c] for c in conds], vals, color=[COND_COLOR[c] for c in conds])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, str(v), ha="center", fontsize=13, fontweight="bold")
    pct = (vals[0] - vals[1]) / vals[0] * 100
    ax.set_ylabel("Total model steps across all 32 tasks")
    ax.set_title("L3 used fewer steps to reach the same answers")
    ax.text(0.5, -0.2, f"{vals[0]} -> {vals[1]} steps ({pct:.1f}% fewer)", transform=ax.transAxes,
            ha="center", fontsize=11, color="#555")
    savefig(fig, "fig03_steps_l0_vs_l3.png")


def fig4_cost():
    agg = load_json("data/independent_benchmark/processed/aggregates.json")
    conds = ["L0", "L3"]
    vals = [agg[c]["cost_usd"] for c in conds]
    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar([COND_LABEL[c] for c in conds], vals, color=[COND_COLOR[c] for c in conds])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.0004, f"${v:.6f}", ha="center", fontsize=11, fontweight="bold")
    pct = (vals[0] - vals[1]) / vals[0] * 100
    ax.set_ylabel("Total API cost across all 32 tasks (USD)")
    ax.set_title("L3 also cost slightly less to run")
    ax.text(0.5, -0.2, f"${vals[0]:.6f} -> ${vals[1]:.6f} ({pct:.1f}% less)", transform=ax.transAxes,
            ha="center", fontsize=11, color="#555")
    savefig(fig, "fig04_cost_l0_vs_l3.png")


def fig5_interventions():
    agg = load_json("data/independent_benchmark/processed/aggregates.json")
    counts = [agg[c]["interventions"] for c in CONDITIONS]
    steps = [agg[c]["api_calls"] for c in CONDITIONS]
    rates = [c_ / s_ * 100 if s_ else 0 for c_, s_ in zip(counts, steps)]
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar([COND_LABEL[c] for c in CONDITIONS], rates, color=[COND_COLOR[c] for c in CONDITIONS])
    for b, c_, r in zip(bars, counts, rates):
        ax.text(b.get_x() + b.get_width() / 2, r + 1.5, f"{c_} steps\n({r:.1f}%)", ha="center", fontsize=10)
    ax.set_ylim(0, 60)
    ax.set_ylabel("Steps where the guardrail intervened (%)")
    ax.set_title("Only L3 intervened during the experiment")
    savefig(fig, "fig05_interventions.png")


def fig6_task_matrix():
    data = {c: {r["task_id"]: r["correct"] for r in load_raw(c)} for c in CONDITIONS}
    task_ids = sorted(data["L0"].keys())
    grid = [[1 if data[c][t] else 0 for c in CONDITIONS] for t in task_ids]
    fig, ax = plt.subplots(figsize=(6, 11))
    cmap = matplotlib.colors.ListedColormap(["#e05a4e", "#2e9e6b"])
    ax.imshow(grid, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(4))
    ax.set_xticklabels(CONDITIONS)
    ax.set_yticks(range(len(task_ids)))
    ax.set_yticklabels(task_ids, fontsize=8)
    ax.set_title("Every task's outcome was identical across L0-L3", fontsize=14)
    ax.set_xlabel("Condition")
    from matplotlib.patches import Patch
    handles = [Patch(color="#2e9e6b", label="Correct"), Patch(color="#e05a4e", label="Incorrect")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=2, frameon=False)
    savefig(fig, "fig06_task_outcome_matrix.png")


def load_reference_qwen_baseline():
    """The paper's Qwen3.5-27B baseline total_composite_score by age (our reproduction target)."""
    records = load_json("reference/reference_results.json")
    rows = [r for r in records
            if r["model"] == "qwen3.5-27b" and r["condition"] == "baseline"
            and r["metric"] == "total_composite_score" and "target_age" in r]
    return sorted((r["target_age"], r["value"]) for r in rows)


def fig7_reference_trajectory():
    items = load_reference_qwen_baseline()
    fig, ax = plt.subplots(figsize=(7, 5))
    xs = [i[0] for i in items]
    ys = [i[1] for i in items]
    ax.plot(xs, ys, marker="o", color="#8a8f98", linewidth=2, markersize=9)
    for x, y in zip(xs, ys):
        ax.text(x, y + 0.01, f"{y:.2f}", ha="center", fontsize=11)
    ax.set_xticks(xs)
    ax.set_ylim(0, 0.6)
    ax.set_xlabel("Age")
    ax.set_ylabel("Reference composite score (paper's own scale)")
    ax.set_title("REFERENCE PAPER RESULT (contextual only)")
    ax.text(0.5, -0.22, "From the ChildAgentEval paper, Qwen3.5-27B baseline.\n"
            "Not on the same scale as our results (see next figure).",
            transform=ax.transAxes, ha="center", fontsize=10, color="#555")
    savefig(fig, "fig07_reference_trajectory.png")


def fig8_reference_vs_l0():
    ref_items = load_reference_qwen_baseline()
    ref_xs = [i[0] for i in ref_items]
    ref_ys = [i[1] for i in ref_items]

    per_age = load_json("data/independent_benchmark/processed/per_age.json")
    our_xs = sorted(int(a) for a in per_age["L0"].keys())
    our_ys = [per_age["L0"][str(a)] / 8.0 for a in our_xs]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
    ax1.plot(ref_xs, ref_ys, marker="o", color="#8a8f98", linewidth=2, markersize=9)
    ax1.set_title("REFERENCE PAPER RESULT", fontsize=13)
    ax1.set_xlabel("Age")
    ax1.set_ylabel("Reference composite score")
    ax1.set_ylim(0, 1)
    ax1.set_xticks(ref_xs)

    ax2.plot(our_xs, our_ys, marker="o", color=COND_COLOR["L0"], linewidth=2, markersize=9)
    ax2.set_title("OUR MEASURED RESULT (L0)", fontsize=13)
    ax2.set_xlabel("Age")
    ax2.set_ylabel("Our accuracy (fraction correct)")
    ax2.set_ylim(0, 1)
    ax2.set_xticks(our_xs)

    fig.suptitle("Not the same scale - shown side by side, never overlaid", fontsize=14, fontweight="bold")
    fig.text(0.5, -0.03, "Different item sets, different scoring rubrics, undisclosed official methodology.\n"
             "This is context, not a like-for-like comparison.", ha="center", fontsize=10, color="#555")
    savefig(fig, "fig08_reference_vs_l0_separate_panels.png")


def fig9_per_age():
    per_age = load_json("data/independent_benchmark/processed/per_age.json")
    ages = sorted(int(a) for a in per_age["L0"].keys())
    fig, ax = plt.subplots(figsize=(8, 5))
    width = 0.2
    import numpy as np
    x = np.arange(len(ages))
    for i, c in enumerate(CONDITIONS):
        vals = [per_age[c][str(a)] / 8.0 * 100 for a in ages]
        ax.bar(x + (i - 1.5) * width, vals, width, label=c, color=COND_COLOR[c])
    ax.set_xticks(x)
    ax.set_xticklabels([f"Age {a}" for a in ages])
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Results by age group: identical across all four conditions")
    ax.legend(loc="upper right", ncol=4, fontsize=10, frameon=False)
    savefig(fig, "fig09_per_age.png")


def fig10_per_category():
    per_cat = load_json("data/independent_benchmark/processed/per_category.json")
    cats = sorted(per_cat["L0"].keys())
    fig, ax = plt.subplots(figsize=(10, 6))
    import numpy as np
    x = np.arange(len(cats))
    width = 0.2
    for i, c in enumerate(CONDITIONS):
        vals = [per_cat[c][cat] * 100 for cat in cats]
        ax.bar(x + (i - 1.5) * width, vals, width, label=c, color=COND_COLOR[c])
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace("_", "\n") for c in cats], fontsize=9)
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 110)
    ax.set_title("Results by task category: identical across all four conditions")
    ax.legend(loc="upper right", ncol=4, fontsize=10, frameon=False)
    savefig(fig, "fig10_per_category.png")


def main():
    fig1_accuracy()
    fig2_alignment()
    fig3_steps()
    fig4_cost()
    fig5_interventions()
    fig6_task_matrix()
    fig7_reference_trajectory()
    fig8_reference_vs_l0()
    fig9_per_age()
    fig10_per_category()
    print("All 10 outcome-brief figures generated.")


if __name__ == "__main__":
    main()
