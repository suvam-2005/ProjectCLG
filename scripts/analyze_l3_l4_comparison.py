"""Analysis pipeline for the L3 vs L4 guardrail comparison.

Reads ONLY the raw data in data/independent_benchmark/raw/L3.jsonl (the existing,
already-validated L3 run) and data/independent_benchmark/raw/L4.jsonl (the fresh L4 run)
— computes nothing from assumption. This is additive: it does not modify or overwrite
any L0-L3 processed/statistics output used by the original outcome brief. Writes to
data/l3_l4_comparison/{processed,statistics}/.
"""
from __future__ import annotations

import json
from pathlib import Path

from childagenteval_research.benchmark.independent_alignment import compute_age_alignment
from childagenteval_research.evaluation.statistics_utils import describe, paired_comparison, welch_t_test

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "independent_benchmark" / "raw"
OUT_PROCESSED = PROJECT_ROOT / "data" / "l3_l4_comparison" / "processed"
OUT_STATS = PROJECT_ROOT / "data" / "l3_l4_comparison" / "statistics"
CONDITIONS = ["L3", "L4"]
AGES = [7, 10, 13, 16]


def load_condition(condition: str) -> list[dict]:
    path = RAW_DIR / f"{condition}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def category_scores_for(rows: list[dict], age: int) -> dict[str, float]:
    return {r["category"]: r["score"] for r in rows if r["target_age"] == age}


def main() -> None:
    OUT_PROCESSED.mkdir(parents=True, exist_ok=True)
    OUT_STATS.mkdir(parents=True, exist_ok=True)

    data = {c: load_condition(c) for c in CONDITIONS}

    # --- data quality checks (same checks analyze_full_benchmark.py runs for L0-L3) ---
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
    (OUT_STATS / "data_quality_report.json").write_text(json.dumps(quality_report, indent=2))
    for c, q in quality_report.items():
        assert q["n_tasks"] == 32, f"{c}: expected 32 tasks, got {q['n_tasks']}"
        assert not q["has_duplicates"], f"{c}: duplicate task_ids found"
        assert q["missing_required_fields"] == 0, f"{c}: missing required fields"
        assert q["negative_tokens"] == 0 and q["negative_cost"] == 0 and q["impossible_scores"] == 0

    # --- per-task outcome identity check: which L3 outcomes did L4 change? ---
    outcomes_by_condition = {c: {r["task_id"]: r["correct"] for r in rows} for c, rows in data.items()}
    identical_to_l3 = sum(1 for tid, correct in outcomes_by_condition["L4"].items() if correct == outcomes_by_condition["L3"][tid])
    flipped_incorrect_to_correct = [
        tid for tid, correct in outcomes_by_condition["L4"].items()
        if correct and not outcomes_by_condition["L3"][tid]
    ]
    flipped_correct_to_incorrect = [
        tid for tid, correct in outcomes_by_condition["L4"].items()
        if not correct and outcomes_by_condition["L3"][tid]
    ]

    # --- capability (task performance) ---
    capability = {c: sum(r["score"] for r in data[c]) / len(data[c]) for c in CONDITIONS}

    # --- alignment (per age, per condition; then condition-level mean) ---
    alignment_by_condition_age = {}
    for c in CONDITIONS:
        for age in AGES:
            cat_scores = category_scores_for(data[c], age)
            result = compute_age_alignment(age, cat_scores)
            alignment_by_condition_age[(c, age)] = result.alignment.overall_alignment
    alignment_condition_level = {c: sum(alignment_by_condition_age[(c, a)] for a in AGES) / len(AGES) for c in CONDITIONS}

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

    # --- statistical comparison: paired (same 32 tasks) L3 vs L4 ---
    l3_scores = [r["score"] for r in sorted(data["L3"], key=lambda r: r["task_id"])]
    l4_scores = [r["score"] for r in sorted(data["L4"], key=lambda r: r["task_id"])]
    paired = paired_comparison(l4_scores, l3_scores)
    ttest = welch_t_test(l4_scores, l3_scores)
    comparison = {
        "n": paired.n,
        "mean_difference": paired.mean_difference,
        "difference_ci_low": paired.difference_ci.low,
        "difference_ci_high": paired.difference_ci.high,
        "cohens_d_paired": paired.cohens_d_paired,
        "welch_t_statistic": ttest.statistic,
        "welch_p_value": ttest.p_value_two_tailed,
    }

    # --- write processed data ---
    (OUT_PROCESSED / "capability.json").write_text(json.dumps(capability, indent=2))
    (OUT_PROCESSED / "alignment_condition_level.json").write_text(json.dumps(alignment_condition_level, indent=2))
    (OUT_PROCESSED / "aggregates.json").write_text(json.dumps(aggregates, indent=2))
    (OUT_PROCESSED / "per_age.json").write_text(json.dumps(per_age, indent=2))
    (OUT_PROCESSED / "per_category.json").write_text(json.dumps(per_category, indent=2))
    (OUT_PROCESSED / "outcome_flips.json").write_text(json.dumps({
        "identical_to_l3_of_32": identical_to_l3,
        "flipped_incorrect_to_correct": flipped_incorrect_to_correct,
        "flipped_correct_to_incorrect": flipped_correct_to_incorrect,
    }, indent=2))

    # --- write statistics ---
    (OUT_STATS / "comparison_l3_vs_l4.json").write_text(json.dumps(comparison, indent=2))
    descriptive = {c: describe([r["score"] for r in data[c]]).__dict__ for c in CONDITIONS}
    (OUT_STATS / "descriptive_scores.json").write_text(json.dumps(descriptive, indent=2))

    print("=== SUMMARY ===")
    print("capability:", capability)
    print("alignment_condition_level:", alignment_condition_level)
    print("identical_to_l3 (of 32):", identical_to_l3)
    print("flipped_incorrect_to_correct:", flipped_incorrect_to_correct)
    print("flipped_correct_to_incorrect:", flipped_correct_to_incorrect)
    print("aggregates:")
    for c in CONDITIONS:
        print(f"  {c}: {aggregates[c]}")
    print("comparison_l3_vs_l4:", json.dumps(comparison, indent=2))
    print("Data quality: all checks passed.")


if __name__ == "__main__":
    main()
