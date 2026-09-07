"""Generates the presentation-styled figures for the L3 vs L4 comparison doc.

Additive: reads data/independent_benchmark/raw/{L3,L4}.jsonl and
data/l3_l4_comparison/processed/, writes to reports/l3_l4_comparison_figures/. Does not
modify or replace the existing L0-L3 outcome-brief figures. Same visual style (same
matplotlib rcParams, same color-by-condition convention) as generate_outcome_brief_figures.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "independent_benchmark" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "l3_l4_comparison" / "processed"
OUT_DIR = PROJECT_ROOT / "reports" / "l3_l4_comparison_figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CONDITIONS = ["L3", "L4"]
COND_LABEL = {
    "L3": "L3\n(process supervisor—wait)",
    "L4": "L4\n(process supervisor—redirect)",
}
COND_COLOR = {"L3": "#2e9e6b", "L4": "#4c8bf5"}

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
    cap = load_json("data/l3_l4_comparison/processed/capability.json")
    vals = [cap[c] * 100 for c in CONDITIONS]
    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar([COND_LABEL[c] for c in CONDITIONS], vals, color=[COND_COLOR[c] for c in CONDITIONS])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.2f}%", ha="center", fontsize=13, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Tasks answered correctly (%)")
    ax.set_title("Accuracy: L3 vs L4")
    savefig(fig, "fig01_accuracy.png")


def fig2_alignment():
    align = load_json("data/l3_l4_comparison/processed/alignment_condition_level.json")
    vals = [align[c] for c in CONDITIONS]
    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar([COND_LABEL[c] for c in CONDITIONS], vals, color=[COND_COLOR[c] for c in CONDITIONS])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.5f}", ha="center", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Cognitive alignment score (0-1 scale, ours only)")
    ax.set_title("Alignment: L3 vs L4")
    savefig(fig, "fig02_alignment.png")


def fig3_steps():
    agg = load_json("data/l3_l4_comparison/processed/aggregates.json")
    vals = [agg[c]["api_calls"] for c in CONDITIONS]
    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar([COND_LABEL[c] for c in CONDITIONS], vals, color=[COND_COLOR[c] for c in CONDITIONS])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, str(v), ha="center", fontsize=13, fontweight="bold")
    pct = (vals[0] - vals[1]) / vals[0] * 100
    ax.set_ylabel("Total model steps across all 32 tasks")
    ax.set_title("Steps: L3 vs L4")
    ax.text(0.5, -0.2, f"{vals[0]} -> {vals[1]} steps ({pct:+.1f}%)", transform=ax.transAxes,
            ha="center", fontsize=11, color="#555")
    savefig(fig, "fig03_steps.png")


def fig4_cost():
    agg = load_json("data/l3_l4_comparison/processed/aggregates.json")
    vals = [agg[c]["cost_usd"] for c in CONDITIONS]
    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar([COND_LABEL[c] for c in CONDITIONS], vals, color=[COND_COLOR[c] for c in CONDITIONS])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.0004, f"${v:.6f}", ha="center", fontsize=11, fontweight="bold")
    pct = (vals[0] - vals[1]) / vals[0] * 100
    ax.set_ylabel("Total API cost across all 32 tasks (USD)")
    ax.set_title("Cost: L3 vs L4")
    ax.text(0.5, -0.2, f"${vals[0]:.6f} -> ${vals[1]:.6f} ({pct:+.1f}%)", transform=ax.transAxes,
            ha="center", fontsize=11, color="#555")
    savefig(fig, "fig04_cost.png")


def fig5_interventions():
    agg = load_json("data/l3_l4_comparison/processed/aggregates.json")
    counts = [agg[c]["interventions"] for c in CONDITIONS]
    steps = [agg[c]["api_calls"] for c in CONDITIONS]
    rates = [c_ / s_ * 100 if s_ else 0 for c_, s_ in zip(counts, steps)]
    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar([COND_LABEL[c] for c in CONDITIONS], rates, color=[COND_COLOR[c] for c in CONDITIONS])
    for b, c_, r in zip(bars, counts, rates):
        ax.text(b.get_x() + b.get_width() / 2, r + 1.5, f"{c_} steps\n({r:.1f}%)", ha="center", fontsize=10)
    ax.set_ylim(0, max(rates) + 15)
    ax.set_ylabel("Steps where the guardrail intervened (%)")
    ax.set_title("Intervention rate: L3 vs L4")
    savefig(fig, "fig05_interventions.png")


def fig6_task_matrix():
    data = {c: {r["task_id"]: r["correct"] for r in load_raw(c)} for c in CONDITIONS}
    task_ids = sorted(data["L3"].keys())
    grid = [[1 if data[c][t] else 0 for c in CONDITIONS] for t in task_ids]
    fig, ax = plt.subplots(figsize=(5, 11))
    cmap = matplotlib.colors.ListedColormap(["#e05a4e", "#2e9e6b"])
    ax.imshow(grid, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(2))
    ax.set_xticklabels(CONDITIONS)
    ax.set_yticks(range(len(task_ids)))
    ax.set_yticklabels(task_ids, fontsize=8)
    ax.set_title("Per-task outcome: L3 vs L4", fontsize=14)
    ax.set_xlabel("Condition")
    from matplotlib.patches import Patch
    handles = [Patch(color="#2e9e6b", label="Correct"), Patch(color="#e05a4e", label="Incorrect")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=2, frameon=False)
    savefig(fig, "fig06_task_outcome_matrix.png")


def fig7_per_age():
    per_age = load_json("data/l3_l4_comparison/processed/per_age.json")
    ages = sorted(int(a) for a in per_age["L3"].keys())
    fig, ax = plt.subplots(figsize=(7, 5))
    width = 0.32
    x = np.arange(len(ages))
    for i, c in enumerate(CONDITIONS):
        vals = [per_age[c][str(a)] / 8.0 * 100 for a in ages]
        ax.bar(x + (i - 0.5) * width, vals, width, label=c, color=COND_COLOR[c])
    ax.set_xticks(x)
    ax.set_xticklabels([f"Age {a}" for a in ages])
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Results by age group: L3 vs L4")
    ax.legend(loc="upper right", ncol=2, fontsize=10, frameon=False)
    savefig(fig, "fig07_per_age.png")


def fig8_per_category():
    per_cat = load_json("data/l3_l4_comparison/processed/per_category.json")
    cats = sorted(per_cat["L3"].keys())
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(cats))
    width = 0.32
    for i, c in enumerate(CONDITIONS):
        vals = [per_cat[c][cat] * 100 for cat in cats]
        ax.bar(x + (i - 0.5) * width, vals, width, label=c, color=COND_COLOR[c])
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace("_", "\n") for c in cats], fontsize=9)
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 110)
    ax.set_title("Results by task category: L3 vs L4")
    ax.legend(loc="upper right", ncol=2, fontsize=10, frameon=False)
    savefig(fig, "fig08_per_category.png")


def main():
    fig1_accuracy()
    fig2_alignment()
    fig3_steps()
    fig4_cost()
    fig5_interventions()
    fig6_task_matrix()
    fig7_per_age()
    fig8_per_category()
    print("All 8 L3-vs-L4 comparison figures generated.")


if __name__ == "__main__":
    main()
