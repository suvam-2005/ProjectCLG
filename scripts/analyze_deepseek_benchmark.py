"""Analysis pipeline for the DeepSeek-V3.2 run of the Independent Interactive
Cognitive-Age Benchmark, conditions L0-L4 analysed together (same design as
scripts/analyze_gemma_benchmark.py). Reads ONLY data/deepseek_benchmark/raw/ — computes
nothing from assumption. Writes processed data and statistical summaries to
data/deepseek_benchmark/{processed,statistics}/. Reports are written separately by hand
from this script's output, same convention as the Qwen and Gemma runs.

The reference paper did not evaluate any DeepSeek model, so there is no reference
comparison. In its place, reference_comparison.json compares DeepSeek's L0 per-age
accuracy with OUR Qwen3.5-27B and Gemma 4 26B A4B L0 runs on this same benchmark, which
share tasks and scoring and are therefore directly comparable.
"""
from __future__ import annotations

import json
from pathlib import Path

from childagenteval_research.benchmark.independent_alignment import compute_age_alignment
from childagenteval_research.evaluation.statistics_utils import (
    bonferroni_correction,
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
DATA_DIR = PROJECT_ROOT / "data" / "deepseek_benchmark"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
STATS_DIR = DATA_DIR / "statistics"
CONDITIONS = ["L0", "L1", "L2", "L3", "L4"]
AGES = [7, 10, 13, 16]

# Our own L0 runs of the other two models on this same benchmark (same tasks, same scoring).
OTHER_MODEL_L0 = {
    "qwen/qwen3.5-27b": PROJECT_ROOT / "data" / "independent_benchmark" / "raw" / "L0.jsonl",
    "google/gemma-4-26b-a4b-it": PROJECT_ROOT / "data" / "gemma_benchmark" / "raw" / "L0.jsonl",
}


def load_condition(condition: str) -> list[dict]:
    path = RAW_DIR / f"{condition}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_trajectory(condition: str, task_id: str) -> list[dict]:
    path = RAW_DIR / "trajectories" / condition / f"{task_id}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def category_scores_for(rows: list[dict], age: int) -> dict[str, float]:
    return {r["category"]: r["score"] for r in rows if r["target_age"] == age}


def paired_stats(a_rows: list[dict], b_rows: list[dict]) -> dict:
    a = sorted(a_rows, key=lambda r: r["task_id"])
    b = sorted(b_rows, key=lambda r: r["task_id"])
    a_scores = [r["score"] for r in a]
    b_scores = [r["score"] for r in b]
    paired = paired_comparison(b_scores, a_scores)
    ttest = welch_t_test(b_scores, a_scores)
    gained = [x["task_id"] for x, y in zip(a, b) if not x["correct"] and y["correct"]]
    lost = [x["task_id"] for x, y in zip(a, b) if x["correct"] and not y["correct"]]
    return {
        "n": paired.n,
        "mean_difference": paired.mean_difference,
        "difference_ci_low": paired.difference_ci.low,
        "difference_ci_high": paired.difference_ci.high,
        "cohens_d_paired": paired.cohens_d_paired,
        "welch_t_statistic": ttest.statistic,
        "welch_p_value": ttest.p_value_two_tailed,
        "discordant_pairs": len(gained) + len(lost),
        "incorrect_to_correct": gained,
        "correct_to_incorrect": lost,
    }


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    STATS_DIR.mkdir(parents=True, exist_ok=True)

    data = {c: load_condition(c) for c in CONDITIONS}

    # --- data quality checks (STOP before conclusions if any of these fail) ---
    quality_report = {}
    for c, rows in data.items():
        ids = [r["task_id"] for r in rows]
        quality_report[c] = {
            "n_tasks": len(rows),
            "n_unique_task_ids": len(set(ids)),
            "has_duplicates": len(ids) != len(set(ids)),
            "models": sorted({r["model"] for r in rows}),
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
        assert q["models"] == ["deepseek/deepseek-v3.2"], f"{c}: unexpected model(s) {q['models']}"
        assert q["missing_required_fields"] == 0, f"{c}: missing required fields"
        assert q["negative_tokens"] == 0 and q["negative_cost"] == 0 and q["impossible_scores"] == 0

    outcomes_by_condition = {c: {r["task_id"]: r["correct"] for r in rows} for c, rows in data.items()}
    identical_to_l0 = {
        c: sum(1 for tid, correct in outcomes_by_condition[c].items() if correct == outcomes_by_condition["L0"][tid])
        for c in CONDITIONS
    }

    capability = {c: sum(r["score"] for r in data[c]) / len(data[c]) for c in CONDITIONS}

    alignment_by_condition_age = {}
    for c in CONDITIONS:
        for age in AGES:
            result = compute_age_alignment(age, category_scores_for(data[c], age))
            alignment_by_condition_age[(c, age)] = result.alignment.overall_alignment
    alignment_condition_level = {
        c: sum(alignment_by_condition_age[(c, a)] for a in AGES) / len(AGES) for c in CONDITIONS
    }

    tradeoff = {}
    for c in CONDITIONS:
        tradeoff[c] = {
            "alignment": alignment_condition_level[c],
            "capability": capability[c],
            "alignment_gain_vs_l0": alignment_gain(alignment_condition_level[c], alignment_condition_level["L0"]),
            "capability_change_vs_l0": capability_change(capability[c], capability["L0"]),
            "capability_retention_vs_l0": relative_capability_retention(capability[c], capability["L0"]),
        }

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
            "latency_s": sum(r["latency_s"] for r in rows),
            "interventions": sum(r["interventions"] for r in rows),
            "errors": sum(r["errors"] for r in rows),
            "recoveries": sum(r["recoveries"] for r in rows),
            "mean_steps": sum(r["steps"] for r in rows) / len(rows),
            "intervention_rate": sum(r["interventions"] for r in rows) / sum(r["steps"] for r in rows),
        }

    # --- intervention triggers + answer-switching, read from the per-step trajectories ---
    behavior = {}
    for c in CONDITIONS:
        triggers: dict[str, int] = {}
        switched_tasks = []
        for r in data[c]:
            records = load_trajectory(c, r["task_id"])
            for rec in records:
                trigger = (rec["action"].get("guardrail_metadata") or {}).get("trigger")
                reason = rec["action"].get("guardrail_reason")
                if rec["action"].get("guardrail_decision") != "allow":
                    key = trigger or reason or "unspecified"
                    triggers[key] = triggers.get(key, 0) + 1
            clicks = [rec["action"]["final"].get("target") for rec in records if rec["action"]["final"].get("action") == "click"]
            distinct = list(dict.fromkeys(t for t in clicks if t and t != "#finish_button"))
            if len(distinct) > 1:
                switched_tasks.append(r["task_id"])
        behavior[c] = {
            "intervention_triggers": triggers,
            "tasks_clicking_more_than_one_distinct_target": len(switched_tasks),
            "task_ids": switched_tasks,
        }

    per_age = {c: {age: sum(1 for r in data[c] if r["target_age"] == age and r["correct"]) for age in AGES} for c in CONDITIONS}
    per_category = {}
    for c in CONDITIONS:
        cats = sorted({r["category"] for r in data[c]})
        per_category[c] = {cat: sum(1 for r in data[c] if r["category"] == cat and r["correct"]) / 4 for cat in cats}

    per_task = {
        tid: {c: outcomes_by_condition[c][tid] for c in CONDITIONS}
        for tid in sorted(outcomes_by_condition["L0"])
    }

    # --- paired comparisons: L0 vs every guardrail, plus L3 vs L4 (same as the Qwen L4 study) ---
    comparisons = {f"L0_vs_{c}": paired_stats(data["L0"], data[c]) for c in ["L1", "L2", "L3", "L4"]}
    comparisons["L3_vs_L4"] = paired_stats(data["L3"], data["L4"])
    # A zero-variance comparison (every task identical) has no p-value; it's reported as
    # p=1.0 here, which is what "no difference at all" means for the correction.
    raw_p = [comparisons[f"L0_vs_{c}"]["welch_p_value"] for c in ["L1", "L2", "L3", "L4"]]
    bonf = bonferroni_correction([1.0 if p is None else p for p in raw_p])
    multiple_comparison = {
        "method": "bonferroni",
        "family": "L0 vs L1/L2/L3/L4",
        "raw_p_values": dict(zip(["L1", "L2", "L3", "L4"], raw_p)),
        "adjusted_p_values": dict(zip(["L1", "L2", "L3", "L4"], bonf.adjusted_p_values)),
        "rejected_at_0.05": dict(zip(["L1", "L2", "L3", "L4"], bonf.reject_null)),
    }

    other_l0 = {}
    for model, path in OTHER_MODEL_L0.items():
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        other_l0[model] = {age: sum(1 for r in rows if r["target_age"] == age and r["correct"]) / 8 for age in AGES}
    reference_comparison = [
        {
            "age": age,
            "our_l0_deepseek_v3_2": per_age["L0"][age] / 8,
            **{f"our_l0_{model}": other_l0[model][age] for model in OTHER_MODEL_L0},
            "note": "all three are OUR results on the same benchmark and scoring; the paper has no DeepSeek result",
        }
        for age in AGES
    ]

    (PROCESSED_DIR / "capability.json").write_text(json.dumps(capability, indent=2))
    (PROCESSED_DIR / "alignment_by_condition_age.json").write_text(
        json.dumps({f"{c}_{a}": v for (c, a), v in alignment_by_condition_age.items()}, indent=2)
    )
    (PROCESSED_DIR / "alignment_condition_level.json").write_text(json.dumps(alignment_condition_level, indent=2))
    (PROCESSED_DIR / "tradeoff.json").write_text(json.dumps(tradeoff, indent=2))
    (PROCESSED_DIR / "aggregates.json").write_text(json.dumps(aggregates, indent=2))
    (PROCESSED_DIR / "guardrail_behavior.json").write_text(json.dumps(behavior, indent=2))
    (PROCESSED_DIR / "per_age.json").write_text(json.dumps(per_age, indent=2))
    (PROCESSED_DIR / "per_category.json").write_text(json.dumps(per_category, indent=2))
    (PROCESSED_DIR / "per_task_outcomes.json").write_text(json.dumps(per_task, indent=2))
    (PROCESSED_DIR / "outcome_identity_vs_l0.json").write_text(json.dumps(identical_to_l0, indent=2))
    (PROCESSED_DIR / "reference_comparison.json").write_text(json.dumps(reference_comparison, indent=2))

    (STATS_DIR / "comparisons.json").write_text(json.dumps(comparisons, indent=2))
    (STATS_DIR / "multiple_comparison.json").write_text(json.dumps(multiple_comparison, indent=2))
    descriptive = {c: describe([r["score"] for r in data[c]]).__dict__ for c in CONDITIONS}
    (STATS_DIR / "descriptive_scores.json").write_text(json.dumps(descriptive, indent=2))

    print("=== SUMMARY ===")
    print("capability:", capability)
    print("alignment_condition_level:", alignment_condition_level)
    print("identical_to_l0 (of 32):", identical_to_l0)
    for c in CONDITIONS:
        print(f"  {c}: {aggregates[c]}")
        print(f"      behavior: {behavior[c]}")
    print("per_age:", per_age)
    print("per_category:", json.dumps(per_category, indent=1))
    print("comparisons:", json.dumps(comparisons, indent=2))
    print("multiple_comparison:", multiple_comparison)
    print("Data quality: all checks passed.")


if __name__ == "__main__":
    main()
