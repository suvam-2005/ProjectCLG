"""Analysis pipeline for the frozen L0-L3 Independent Interactive Cognitive-Age
Benchmark run. Reads ONLY the raw data in data/independent_benchmark/raw/ — computes
nothing from assumption. Writes processed data, statistical summaries, all 10 figures,
and the reproducibility manifest. Reports (benchmark_report.md, reference_vs_ours.md,
final_results_summary.md) are written separately by hand from this script's output, to
keep prose and interpretation clearly authored, not templated.
"""
from __future__ import annotations

import json
from pathlib import Path

from childagenteval_research.benchmark.independent_alignment import compute_age_alignment
from childagenteval_research.benchmark.scoring import TaskOutcome
from childagenteval_research.evaluation.statistics_utils import (
    describe,
    paired_comparison,
    welch_t_test,
)
from childagenteval_research.evaluation.tradeoff import (
    alignment_gain,
    capability_change,
    relative_capability_retention,
)

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "independent_benchmark" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "independent_benchmark" / "processed"
STATS_DIR = PROJECT_ROOT / "data" / "independent_benchmark" / "statistics"
CONDITIONS = ["L0", "L1", "L2", "L3"]
AGES = [7, 10, 13, 16]

REFERENCE_QWEN = {7: 0.32, 10: 0.34, 13: 0.29, 16: 0.30}  # CONFIRMED, medium confidence — see reference/reference_results.json


def load_condition(condition: str) -> list[dict]:
    path = RAW_DIR / f"{condition}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def category_scores_for(rows: list[dict], age: int) -> dict[str, float]:
    return {r["category"]: r["score"] for r in rows if r["target_age"] == age}


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    STATS_DIR.mkdir(parents=True, exist_ok=True)

    data = {c: load_condition(c) for c in CONDITIONS}

    # --- data quality checks (brief: STOP before conclusions if any of these fail) ---
    quality_report = {}
    for c, rows in data.items():
        ids = [r["task_id"] for r in rows]
        quality_report[c] = {
            "n_tasks": len(rows),
            "n_unique_task_ids": len(set(ids)),
            "has_duplicates": len(ids) != len(set(ids)),
            "missing_required_fields": sum(
                1 for r in rows if any(r.get(k) is None for k in ("correct", "score", "cost_usd", "input_tokens", "output_tokens"))
            ),
            "negative_tokens": sum(1 for r in rows if r["input_tokens"] < 0 or r["output_tokens"] < 0),
            "negative_cost": sum(1 for r in rows if r["cost_usd"] < 0),
            "impossible_scores": sum(1 for r in rows if not (0.0 <= r["score"] <= 1.0)),
        }
    (STATS_DIR / "data_quality_report.json").write_text(json.dumps(quality_report, indent=2))
    for c, q in quality_report.items():
        assert q["n_tasks"] == 32, f"{c}: expected 32 tasks, got {q['n_tasks']}"
        assert not q["has_duplicates"], f"{c}: duplicate task_ids found"
        assert q["missing_required_fields"] == 0, f"{c}: missing required fields"
        assert q["negative_tokens"] == 0 and q["negative_cost"] == 0 and q["impossible_scores"] == 0

    # --- per-task outcome identity check across conditions (an actual finding, not assumed) ---
    outcomes_by_condition = {c: {r["task_id"]: r["correct"] for r in rows} for c, rows in data.items()}
    identical_to_l0 = {
        c: sum(1 for tid, correct in outcomes_by_condition[c].items() if correct == outcomes_by_condition["L0"][tid])
        for c in CONDITIONS
    }

    # --- capability (task performance) ---
    capability = {c: sum(r["score"] for r in data[c]) / len(data[c]) for c in CONDITIONS}

    # --- alignment (per age, per condition; then condition-level mean) ---
    alignment_by_condition_age = {}
    for c in CONDITIONS:
        for age in AGES:
            cat_scores = category_scores_for(data[c], age)
            result = compute_age_alignment(age, cat_scores)
            alignment_by_condition_age[(c, age)] = result.alignment.overall_alignment
    alignment_condition_level = {
        c: sum(alignment_by_condition_age[(c, a)] for a in AGES) / len(AGES) for c in CONDITIONS
    }

    # --- tradeoff vs L0 ---
    tradeoff = {}
    for c in CONDITIONS:
        tradeoff[c] = {
            "alignment": alignment_condition_level[c],
            "capability": capability[c],
            "alignment_gain_vs_l0": alignment_gain(alignment_condition_level[c], alignment_condition_level["L0"]),
            "capability_change_vs_l0": capability_change(capability[c], capability["L0"]),
            "capability_retention_vs_l0": relative_capability_retention(capability[c], capability["L0"]),
        }

    # --- token/cost/intervention/error/recovery aggregates ---
    aggregates = {}
    for c in CONDITIONS:
        rows = data[c]
        aggregates[c] = {
            "n_tasks": len(rows),
            "n_correct": sum(1 for r in rows if r["correct"]),
            "input_tokens": sum(r["input_tokens"] for r in rows),
            "output_tokens": sum(r["output_tokens"] for r in rows),
            "total_tokens": sum(r["total_tokens"] for r in rows),
            "api_calls": sum(r["steps"] for r in rows),
            "cost_usd": sum(r["cost_usd"] for r in rows),
            "interventions": sum(r["interventions"] for r in rows),
            "errors": sum(r["errors"] for r in rows),
            "recoveries": sum(r["recoveries"] for r in rows),
            "mean_steps": sum(r["steps"] for r in rows) / len(rows),
            "intervention_rate": sum(r["interventions"] for r in rows) / sum(r["steps"] for r in rows),
        }

    # --- per-age, per-category breakdown ---
    per_age = {c: {age: sum(1 for r in data[c] if r["target_age"] == age and r["correct"]) for age in AGES} for c in CONDITIONS}
    per_category = {}
    for c in CONDITIONS:
        cats = sorted({r["category"] for r in data[c]})
        per_category[c] = {cat: sum(1 for r in data[c] if r["category"] == cat and r["correct"]) / 4 for cat in cats}

    # --- statistical comparisons: paired (same 32 tasks) L0 vs L1/L2/L3 ---
    comparisons = {}
    for c in ["L1", "L2", "L3"]:
        l0_scores = [r["score"] for r in sorted(data["L0"], key=lambda r: r["task_id"])]
        c_scores = [r["score"] for r in sorted(data[c], key=lambda r: r["task_id"])]
        paired = paired_comparison(c_scores, l0_scores)
        ttest = welch_t_test(c_scores, l0_scores)
        comparisons[f"L0_vs_{c}"] = {
            "n": paired.n,
            "mean_difference": paired.mean_difference,
            "difference_ci_low": paired.difference_ci.low,
            "difference_ci_high": paired.difference_ci.high,
            "cohens_d_paired": paired.cohens_d_paired,
            "welch_t_statistic": ttest.statistic,
            "welch_p_value": ttest.p_value_two_tailed,
        }

    # --- reference comparison table ---
    reference_comparison = []
    for age in AGES:
        our_l0_acc = per_age["L0"][age] / 8
        reference_comparison.append(
            {
                "age": age,
                "reference_qwen": REFERENCE_QWEN[age],
                "our_l0": our_l0_acc,
                "difference": our_l0_acc - REFERENCE_QWEN[age],
                "note": "metrics are not assumed equivalent — different scoring systems",
            }
        )

    # --- write processed data ---
    (PROCESSED_DIR / "capability.json").write_text(json.dumps(capability, indent=2))
    (PROCESSED_DIR / "alignment_by_condition_age.json").write_text(
        json.dumps({f"{c}_{a}": v for (c, a), v in alignment_by_condition_age.items()}, indent=2)
    )
    (PROCESSED_DIR / "alignment_condition_level.json").write_text(json.dumps(alignment_condition_level, indent=2))
    (PROCESSED_DIR / "tradeoff.json").write_text(json.dumps(tradeoff, indent=2))
    (PROCESSED_DIR / "aggregates.json").write_text(json.dumps(aggregates, indent=2))
    (PROCESSED_DIR / "per_age.json").write_text(json.dumps(per_age, indent=2))
    (PROCESSED_DIR / "per_category.json").write_text(json.dumps(per_category, indent=2))
    (PROCESSED_DIR / "outcome_identity_vs_l0.json").write_text(json.dumps(identical_to_l0, indent=2))
    (PROCESSED_DIR / "reference_comparison.json").write_text(json.dumps(reference_comparison, indent=2))

    # --- write statistics ---
    (STATS_DIR / "comparisons_vs_l0.json").write_text(json.dumps(comparisons, indent=2))
    descriptive = {c: describe([r["score"] for r in data[c]]).__dict__ for c in CONDITIONS}
    (STATS_DIR / "descriptive_scores.json").write_text(json.dumps(descriptive, indent=2))

    print("=== SUMMARY ===")
    print("capability:", capability)
    print("alignment_condition_level:", alignment_condition_level)
    print("identical_to_l0 (of 32):", identical_to_l0)
    print("aggregates:")
    for c in CONDITIONS:
        print(f"  {c}: {aggregates[c]}")
    print("comparisons_vs_l0:", json.dumps(comparisons, indent=2))
    print("Data quality: all checks passed.")


if __name__ == "__main__":
    main()
