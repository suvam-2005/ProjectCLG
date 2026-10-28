"""Generates both figure sets for the Gemma 4 26B A4B run, with ALL FIVE conditions
(L0, L1, L2, L3, L4) on every shared graph — unlike the Qwen deliverables, where the
L0-L3 figures and the L3-vs-L4 figures were produced as separate sets.

  reports/gemma/figures/         — 10 research-report figures (+ captions.json),
                                   same numbering/meaning as reports/figures/
  reports/gemma/outcome_figures/ — 10 presentation figures, same numbering/meaning as
                                   reports/outcome_figures/

Every number plotted is read from data/gemma_benchmark/{raw,processed}/ and
reference/reference_results.json. Titles describe what is plotted rather than
asserting a conclusion, since they are generated before anyone reads the result.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from childagenteval_research.evaluation.statistics_utils import describe

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "gemma_benchmark"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = PROJECT_ROOT / "reports" / "gemma" / "figures"
OUTCOME_DIR = PROJECT_ROOT / "reports" / "gemma" / "outcome_figures"

MODEL_LABEL = "Gemma 4 26B A4B"
CONDITIONS = ["L0", "L1", "L2", "L3", "L4"]
AGES = [7, 10, 13, 16]
COND_LABEL = {
    "L0": "L0\n(no guardrail)",
    "L1": "L1\n(answer checker)",
    "L2": "L2\n(action checker)",
    "L3": "L3\n(process supervisor)",
    "L4": "L4\n(stop on repeat)",
}
# L0-L3 colours match the Qwen outcome brief; L4 gets the purple used for it in the
# Qwen L3-vs-L4 and L0-to-L5 reports.
COND_COLOR = {"L0": "#8a8f98", "L1": "#4c8bf5", "L2": "#f5a623", "L3": "#2e9e6b", "L4": "#8a4cf5"}

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


def load(name: str):
    return json.loads((PROCESSED_DIR / name).read_text(encoding="utf-8"))


def load_raw(condition: str) -> list[dict]:
    path = RAW_DIR / f"{condition}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_reference_gemma():
    """The paper's Gemma-4-31B baseline (a DIFFERENT variant from the 26B-A4B run here)."""
    records = json.loads((PROJECT_ROOT / "reference" / "reference_results.json").read_text(encoding="utf-8"))
    rows = [r for r in records
            if r["model"] == "gemma-4-31b" and r["condition"] == "baseline"
            and r["metric"] == "total_composite_score" and "target_age" in r]
    return sorted((r["target_age"], r["value"]) for r in rows)


def save(fig, directory: Path, name: str):
    fig.tight_layout()
    fig.savefig(directory / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", directory / name)


def bar_by_condition(ax, values, fmt, offset, yerr=None, short_labels=False):
    labels = CONDITIONS if short_labels else [COND_LABEL[c] for c in CONDITIONS]
    bars = ax.bar(labels, values, color=[COND_COLOR[c] for c in CONDITIONS],
                  yerr=yerr, capsize=5 if yerr is not None else 0)
    if not short_labels:
        ax.tick_params(axis="x", labelsize=10)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + offset, fmt(v), ha="center", fontsize=10, fontweight="bold")
    return bars


def grouped_bars(ax, groups, series_by_condition, scale=1.0):
    x = np.arange(len(groups))
    width = 0.8 / len(CONDITIONS)
    for i, c in enumerate(CONDITIONS):
        ax.bar(x + (i - (len(CONDITIONS) - 1) / 2) * width, [v * scale for v in series_by_condition[c]],
               width, label=c, color=COND_COLOR[c])
    ax.set_xticks(x)
    return x


def sem(values):
    stats = describe(values)
    return stats.stdev / (len(values) ** 0.5) if stats.stdev is not None else 0


# --------------------------------------------------------------------------- research figures

def research_figures():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    capability = load("capability.json")
    alignment_condition = load("alignment_condition_level.json")
    alignment_by_age = load("alignment_by_condition_age.json")
    tradeoff = load("tradeoff.json")
    aggregates = load("aggregates.json")
    per_age = load("per_age.json")
    per_category = load("per_category.json")
    reference = load_reference_gemma()
    captions = {}

    # Figure 1: reference trajectory (Gemma-4-31B — different variant)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot([a for a, _ in reference], [v for _, v in reference], marker="o", color="#8a8f98")
    ax.set_xticks(AGES)
    ax.set_xlabel("Target age")
    ax.set_ylabel("Reference total composite score")
    ax.set_title("Reference paper — reported result (Gemma-4-31B)", fontsize=13)
    save(fig, FIGURES_DIR, "figure1_reference_trajectory.png")
    captions["1"] = ("Figure 1. Reference paper's reported age trajectory for Gemma-4-31B (the paper did not "
                     "evaluate Gemma 4 26B A4B). X-axis: target age (7, 10, 13, 16). Y-axis: reference total "
                     "composite score (paper's own scale; low confidence, single extraction pass — see "
                     "reference/reference_results.json). No CIs reported by the paper (n=4).")

    # Figure 2: reference vs our L0
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(AGES, [v for _, v in reference], marker="o", color="#8a8f98", label="Reference (Gemma-4-31B, paper)")
    ax.plot(AGES, [per_age["L0"][str(a)] / 8 for a in AGES], marker="o", color=COND_COLOR["L0"],
            linestyle="--", label=f"Our L0 ({MODEL_LABEL}, independent benchmark)")
    ax.set_xticks(AGES)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Target age")
    ax.set_ylabel("Score (NOT the same metric)")
    ax.set_title("Reference vs Our L0 — context only, metrics not equivalent", fontsize=12)
    ax.legend(fontsize=9)
    save(fig, FIGURES_DIR, "figure2_reference_vs_l0.png")
    captions["2"] = ("Figure 2. Reference vs our L0 (contextual comparison only). Reference: the paper's composite "
                     "score for Gemma-4-31B; ours: independent-benchmark binary accuracy for Gemma 4 26B A4B, n=8 "
                     "tasks per age. Different model variant, item set and scoring — not statistically comparable.")

    # Figure 3 (PRIMARY): alignment, SEM across n=4 ages
    fig, ax = plt.subplots(figsize=(8, 5))
    vals = [alignment_condition[c] for c in CONDITIONS]
    errs = [sem([alignment_by_age[f"{c}_{a}"] for a in AGES]) for c in CONDITIONS]
    bar_by_condition(ax, vals, lambda v: f"{v:.4f}", 0.03, yerr=errs, short_labels=True)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Condition")
    ax.set_ylabel("Alignment score")
    ax.set_title("PRIMARY: Independent Cognitive Alignment by Condition\n(error bars = SEM, n=4 ages)", fontsize=13)
    save(fig, FIGURES_DIR, "figure3_primary_alignment.png")
    captions["3"] = ("Figure 3. L0 vs L1 vs L2 vs L3 vs L4 cognitive alignment (PRIMARY). Y-axis: independent "
                     "alignment score [0,1] (independent_alignment.py formula), mean across 4 ages. "
                     "Error bars = SEM across n=4 ages.")

    # Figure 4: capability, SEM across n=32 tasks
    fig, ax = plt.subplots(figsize=(8, 5))
    vals = [capability[c] for c in CONDITIONS]
    errs = [sem([r["score"] for r in load_raw(c)]) for c in CONDITIONS]
    bar_by_condition(ax, vals, lambda v: f"{v:.4f}", 0.03, yerr=errs, short_labels=True)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("Condition")
    ax.set_ylabel("Task capability (accuracy)")
    ax.set_title("Task Capability by Condition\n(error bars = SEM, n=32 tasks)", fontsize=13)
    save(fig, FIGURES_DIR, "figure4_capability.png")
    captions["4"] = ("Figure 4. L0-L4 task capability. Y-axis: fraction of the 32 tasks answered correctly [0,1]. "
                     "Error bars = SEM of the binary per-task scores, n=32 tasks per condition.")

    # Figure 5: alignment vs capability retention
    fig, ax = plt.subplots(figsize=(7, 5))
    points: dict[tuple, list[str]] = {}
    for c in CONDITIONS:
        x, y = tradeoff[c]["capability_retention_vs_l0"], alignment_condition[c]
        points.setdefault((round(x, 9), round(y, 9)), []).append(c)
    for (x, y), conds in points.items():
        # Conditions with identical values are drawn as nested rings so none is hidden.
        for i, c in enumerate(conds):
            ax.scatter([x], [y], s=110 + 160 * (len(conds) - 1 - i), color=COND_COLOR[c],
                       label=c, zorder=3 + i, edgecolors="white", linewidths=1.5)
        ax.annotate(" = ".join(conds), (x, y), textcoords="offset points", xytext=(10, 8), fontsize=10)
    ax.set_xlabel("Task capability retention relative to L0")
    ax.set_ylabel("Cognitive alignment score")
    ax.set_title("Alignment vs Capability Retention", fontsize=13)
    ax.legend(fontsize=9)
    save(fig, FIGURES_DIR, "figure5_alignment_vs_retention.png")
    captions["5"] = ("Figure 5. Alignment vs capability retention, one point per condition (L0-L4). X-axis: accuracy "
                     "divided by L0 accuracy. Y-axis: alignment score [0,1]. Coinciding points overlap exactly.")

    # Figure 6: per-age, one line per condition
    fig, ax = plt.subplots(figsize=(8, 5))
    for c in CONDITIONS:
        ax.plot(AGES, [per_age[c][str(a)] / 8 for a in AGES], marker="o", color=COND_COLOR[c], label=c)
    ax.set_xticks(AGES)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Target age")
    ax.set_ylabel("Accuracy")
    ax.set_title("Per-Age Accuracy, L0 vs L1 vs L2 vs L3 vs L4", fontsize=13)
    ax.legend(fontsize=9)
    save(fig, FIGURES_DIR, "figure6_per_age.png")
    captions["6"] = ("Figure 6. Per-age L0-L4 comparison. Y-axis: accuracy, n=8 tasks per age per condition. "
                     "One line per condition; overlapping lines indicate identical values.")

    # Figure 7: per-category
    categories = sorted(per_category["L0"].keys())
    fig, ax = plt.subplots(figsize=(11, 5))
    grouped_bars(ax, categories, {c: [per_category[c][cat] for cat in categories] for c in CONDITIONS})
    ax.set_xticklabels(categories, rotation=30, ha="right")
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("Category")
    ax.set_ylabel("Accuracy")
    ax.set_title("Per-Category Accuracy, L0 vs L1 vs L2 vs L3 vs L4", fontsize=13)
    ax.legend(ncol=5, fontsize=9)
    save(fig, FIGURES_DIR, "figure7_per_category.png")
    captions["7"] = ("Figure 7. Per-category performance. Y-axis: accuracy, n=4 tasks per category per condition. "
                     "One bar series per condition (L0-L4).")

    # Figure 8: intervention rate
    fig, ax = plt.subplots(figsize=(8, 5))
    bar_by_condition(ax, [aggregates[c]["intervention_rate"] for c in CONDITIONS], lambda v: f"{v:.3f}", 0.01, short_labels=True)
    ax.set_xlabel("Condition")
    ax.set_ylabel("Interventions / total steps")
    ax.set_title("Guardrail Intervention Rate by Condition", fontsize=13)
    save(fig, FIGURES_DIR, "figure8_intervention_rate.png")
    captions["8"] = ("Figure 8. Guardrail intervention rate, L0-L4. Y-axis: interventions / total steps [0,1], "
                     "over all 32 tasks' full step counts per condition.")

    # Figure 9: errors / recoveries / mean steps
    fig, ax = plt.subplots(figsize=(11, 5))
    series = {
        "Errors (count)": [aggregates[c]["errors"] for c in CONDITIONS],
        "Recoveries (count)": [aggregates[c]["recoveries"] for c in CONDITIONS],
        "Mean steps/task": [aggregates[c]["mean_steps"] for c in CONDITIONS],
    }
    x = np.arange(len(CONDITIONS))
    width = 0.8 / len(series)
    for i, (label, vals) in enumerate(series.items()):
        ax.bar(x + (i - 1) * width, vals, width, label=label)
    ax.set_xticks(x)
    ax.set_xticklabels(CONDITIONS)
    ax.set_xlabel("Condition")
    ax.set_ylabel("Count / mean steps")
    ax.set_title("Errors, Recoveries, and Mean Trajectory Length", fontsize=13)
    ax.legend(fontsize=9)
    save(fig, FIGURES_DIR, "figure9_errors_recovery_trajectory.png")
    captions["9"] = ("Figure 9. Errors / recoveries / trajectory length, L0-L4. Counts of malformed-output errors "
                     "and recoveries, and mean steps per task, n=32 tasks per condition.")

    # Figure 10: tokens and cost, two panels
    fig, (ax_tok, ax_cost) = plt.subplots(1, 2, figsize=(12, 4.5))
    ax_tok.bar(CONDITIONS, [aggregates[c]["total_tokens"] for c in CONDITIONS], color=[COND_COLOR[c] for c in CONDITIONS])
    ax_tok.set_title("Total tokens", fontsize=13)
    ax_tok.set_xlabel("Condition")
    ax_tok.set_ylabel("Tokens")
    ax_cost.bar(CONDITIONS, [aggregates[c]["cost_usd"] for c in CONDITIONS], color=[COND_COLOR[c] for c in CONDITIONS])
    ax_cost.set_title("Inference cost (USD)", fontsize=13)
    ax_cost.set_xlabel("Condition")
    ax_cost.set_ylabel("USD")
    fig.suptitle("Token Usage and Inference Cost by Condition", fontsize=14, fontweight="bold")
    save(fig, FIGURES_DIR, "figure10_tokens_cost.png")
    captions["10"] = ("Figure 10. Inference cost and token consumption, L0-L4 (two panels). Direct sums of recorded "
                      "usage over 32 tasks, not sampled statistics — no error bars.")

    (FIGURES_DIR / "captions.json").write_text(json.dumps(captions, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- outcome-brief figures

def outcome_figures():
    OUTCOME_DIR.mkdir(parents=True, exist_ok=True)
    cap = load("capability.json")
    align = load("alignment_condition_level.json")
    agg = load("aggregates.json")
    per_age = load("per_age.json")
    per_cat = load("per_category.json")

    # fig01 accuracy
    fig, ax = plt.subplots(figsize=(11, 5))
    bar_by_condition(ax, [cap[c] * 100 for c in CONDITIONS], lambda v: f"{v:.2f}%", 1.5)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Tasks answered correctly (%)")
    ax.set_title("Task accuracy by guardrail level")
    counts = ", ".join(f"{c} {agg[c]['n_correct']}/32" for c in CONDITIONS)
    ax.text(0.5, -0.25, f"{MODEL_LABEL}. Correct of 32: {counts}", transform=ax.transAxes, ha="center", fontsize=10, color="#555")
    save(fig, OUTCOME_DIR, "fig01_accuracy.png")

    # fig02 alignment
    fig, ax = plt.subplots(figsize=(11, 5))
    bar_by_condition(ax, [align[c] for c in CONDITIONS], lambda v: f"{v:.5f}", 0.02)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Cognitive alignment (0-1, ours only)")
    ax.set_title("Cognitive alignment by guardrail level")
    ax.text(0.5, -0.27, "Alignment measures how closely scores tracked our own age-difficulty curve.\n"
            "This is our own [0,1] scale, not the reference paper's scale.",
            transform=ax.transAxes, ha="center", fontsize=10, color="#555")
    save(fig, OUTCOME_DIR, "fig02_alignment.png")

    # fig03 steps (all five — the Qwen brief showed only L0 vs L3 here)
    fig, ax = plt.subplots(figsize=(11, 5))
    steps = [agg[c]["api_calls"] for c in CONDITIONS]
    bar_by_condition(ax, steps, str, max(steps) * 0.015)
    ax.set_ylabel("Total model steps across all 32 tasks")
    ax.set_title("Steps needed to reach an answer")
    ax.text(0.5, -0.25, "  ".join(f"{c}: {(s - steps[0]) / steps[0] * 100:+.1f}% vs L0" for c, s in zip(CONDITIONS[1:], steps[1:])),
            transform=ax.transAxes, ha="center", fontsize=10, color="#555")
    save(fig, OUTCOME_DIR, "fig03_steps.png")

    # fig04 cost
    fig, ax = plt.subplots(figsize=(11, 5))
    costs = [agg[c]["cost_usd"] for c in CONDITIONS]
    bar_by_condition(ax, costs, lambda v: f"${v:.5f}", max(costs) * 0.015)
    ax.set_ylabel("Total API cost across all 32 tasks (USD)")
    ax.set_title("Cost to run each condition")
    ax.text(0.5, -0.25, "  ".join(f"{c}: {(v - costs[0]) / costs[0] * 100:+.1f}% vs L0" for c, v in zip(CONDITIONS[1:], costs[1:])),
            transform=ax.transAxes, ha="center", fontsize=10, color="#555")
    save(fig, OUTCOME_DIR, "fig04_cost.png")

    # fig05 interventions
    fig, ax = plt.subplots(figsize=(11, 5))
    counts = [agg[c]["interventions"] for c in CONDITIONS]
    rates = [agg[c]["intervention_rate"] * 100 for c in CONDITIONS]
    bars = ax.bar([COND_LABEL[c] for c in CONDITIONS], rates, color=[COND_COLOR[c] for c in CONDITIONS])
    ax.tick_params(axis="x", labelsize=10)
    for b, n, r in zip(bars, counts, rates):
        ax.text(b.get_x() + b.get_width() / 2, r + 1.5, f"{n} steps\n({r:.1f}%)", ha="center", fontsize=10)
    ax.set_ylim(0, max(60, max(rates) + 15))
    ax.set_ylabel("Steps where the guardrail intervened (%)")
    ax.set_title("How often each guardrail intervened")
    save(fig, OUTCOME_DIR, "fig05_interventions.png")

    # fig06 task outcome matrix
    data = {c: {r["task_id"]: r["correct"] for r in load_raw(c)} for c in CONDITIONS}
    task_ids = sorted(data["L0"].keys())
    grid = [[1 if data[c][t] else 0 for c in CONDITIONS] for t in task_ids]
    differing = sum(1 for row in grid if len(set(row)) > 1)
    fig, ax = plt.subplots(figsize=(7, 11))
    ax.imshow(grid, aspect="auto", cmap=matplotlib.colors.ListedColormap(["#e05a4e", "#2e9e6b"]), vmin=0, vmax=1)
    ax.set_xticks(range(len(CONDITIONS)))
    ax.set_xticklabels(CONDITIONS)
    ax.set_yticks(range(len(task_ids)))
    ax.set_yticklabels(task_ids, fontsize=8)
    ax.set_title(f"Task-by-task outcome, L0-L4\n({differing} of 32 tasks differ across conditions)", fontsize=13)
    ax.set_xlabel("Condition")
    ax.legend(handles=[Patch(color="#2e9e6b", label="Correct"), Patch(color="#e05a4e", label="Incorrect")],
              loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=2, frameon=False)
    save(fig, OUTCOME_DIR, "fig06_task_outcome_matrix.png")

    # fig07 reference trajectory
    reference = load_reference_gemma()
    fig, ax = plt.subplots(figsize=(7, 5))
    xs, ys = [a for a, _ in reference], [v for _, v in reference]
    ax.plot(xs, ys, marker="o", color="#8a8f98", linewidth=2, markersize=9)
    for x, y in zip(xs, ys):
        ax.text(x, y + 0.01, f"{y:.2f}", ha="center", fontsize=11)
    ax.set_xticks(xs)
    ax.set_ylim(0, 0.6)
    ax.set_xlabel("Age")
    ax.set_ylabel("Reference composite score (paper's scale)")
    ax.set_title("REFERENCE PAPER RESULT (contextual only)")
    ax.text(0.5, -0.25, "From the ChildAgentEval paper, Gemma-4-31B baseline — the paper did not test 26B A4B.\n"
            "Low confidence (single extraction pass). Not on the same scale as our results.",
            transform=ax.transAxes, ha="center", fontsize=10, color="#555")
    save(fig, OUTCOME_DIR, "fig07_reference_trajectory.png")

    # fig08 reference vs L0, separate panels
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
    ax1.plot(xs, ys, marker="o", color="#8a8f98", linewidth=2, markersize=9)
    ax1.set_title("REFERENCE (Gemma-4-31B)", fontsize=13)
    ax1.set_xlabel("Age")
    ax1.set_ylabel("Reference composite score")
    ax1.set_ylim(0, 1)
    ax1.set_xticks(xs)
    ax2.plot(AGES, [per_age["L0"][str(a)] / 8 for a in AGES], marker="o", color=COND_COLOR["L0"], linewidth=2, markersize=9)
    ax2.set_title(f"OUR RESULT (L0, {MODEL_LABEL})", fontsize=13)
    ax2.set_xlabel("Age")
    ax2.set_ylabel("Our accuracy (fraction correct)")
    ax2.set_ylim(0, 1)
    ax2.set_xticks(AGES)
    fig.suptitle("Not the same scale or model variant — shown side by side, never overlaid", fontsize=14, fontweight="bold")
    fig.text(0.5, -0.03, "Different item sets, scoring rubrics and model size; undisclosed official methodology.\n"
             "This is context, not a like-for-like comparison.", ha="center", fontsize=10, color="#555")
    save(fig, OUTCOME_DIR, "fig08_reference_vs_l0_separate_panels.png")

    # fig09 per age
    fig, ax = plt.subplots(figsize=(10, 5))
    grouped_bars(ax, AGES, {c: [per_age[c][str(a)] / 8 for a in AGES] for c in CONDITIONS}, scale=100)
    ax.set_xticklabels([f"Age {a}" for a in AGES])
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 115)
    ax.set_title("Results by age group, L0-L4")
    ax.legend(loc="upper right", ncol=5, fontsize=10, frameon=False)
    save(fig, OUTCOME_DIR, "fig09_per_age.png")

    # fig10 per category
    cats = sorted(per_cat["L0"].keys())
    fig, ax = plt.subplots(figsize=(12, 6))
    grouped_bars(ax, cats, {c: [per_cat[c][cat] for cat in cats] for c in CONDITIONS}, scale=100)
    ax.set_xticklabels([c.replace("_", "\n") for c in cats], fontsize=9)
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 115)
    ax.set_title("Results by task category, L0-L4")
    ax.legend(loc="upper right", ncol=5, fontsize=10, frameon=False)
    save(fig, OUTCOME_DIR, "fig10_per_category.png")


def main():
    research_figures()
    outcome_figures()
    print("All 20 Gemma figures generated (10 research + 10 outcome-brief).")


if __name__ == "__main__":
    main()
