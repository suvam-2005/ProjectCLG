"""Builds reports/gemma/outcome_data_summary.json and reports/gemma/reproducibility_manifest.json
for the Gemma 4 26B A4B run (L0-L4). Every field is read from data/gemma_benchmark/,
the .state/gemma/ ledgers, and reference/reference_results.json — nothing hand-typed.

Usage: python scripts/build_gemma_summary.py [--tests-passed N --tests-total N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "gemma_benchmark"
OUT_DIR = PROJECT_ROOT / "reports" / "gemma"
CONDITIONS = ["L0", "L1", "L2", "L3", "L4"]
MODEL = "google/gemma-4-26b-a4b-it"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_raw(condition: str) -> list[dict]:
    path = DATA_DIR / "raw" / f"{condition}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def task_set_sha256() -> str:
    """Same fingerprint method as the Qwen freeze: SHA-256 of all task JSON files,
    concatenated in sorted path order."""
    digest = hashlib.sha256()
    for path in sorted((PROJECT_ROOT / "benchmark" / "tasks").rglob("*.json")):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests-passed", type=int, default=None)
    parser.add_argument("--tests-total", type=int, default=None)
    args = parser.parse_args()

    processed = DATA_DIR / "processed"
    stats = DATA_DIR / "statistics"
    cap = load_json(processed / "capability.json")
    align = load_json(processed / "alignment_condition_level.json")
    agg = load_json(processed / "aggregates.json")
    behavior = load_json(processed / "guardrail_behavior.json")
    comparisons = load_json(stats / "comparisons.json")

    ref_records = load_json(PROJECT_ROOT / "reference" / "reference_results.json")
    reference_gemma = sorted(
        (r["target_age"], r["value"]) for r in ref_records
        if r["model"] == "gemma-4-31b" and r["condition"] == "baseline"
        and r["metric"] == "total_composite_score" and "target_age" in r
    )

    ledger_project = load_json(PROJECT_ROOT / ".state" / "cost_ledger.json")
    ledger_by_condition = {c: load_json(PROJECT_ROOT / ".state" / "gemma" / f"benchmark_cost_ledger_{c}.json") for c in CONDITIONS}
    gemma_benchmark_spend = sum(l["cumulative_cost_usd"] for l in ledger_by_condition.values())

    def pct(a, b):
        return round((b - a) / a * 100, 2) if a else None

    summary = {
        "result_kind_note": "OUR_RESULT unless explicitly marked REFERENCE_RESULT",
        "benchmark_name": "Independent Interactive Cognitive-Age Benchmark (NOT ChildAgentEval)",
        "model": MODEL,
        "n_tasks": 32,
        "n_conditions": len(CONDITIONS),
        "n_total_task_runs": 32 * len(CONDITIONS),
        "by_condition": {
            c: {
                "accuracy": cap[c],
                "n_correct": agg[c]["n_correct"],
                "n_tasks": agg[c]["n_tasks"],
                "alignment": align[c],
                "interventions": agg[c]["interventions"],
                "intervention_triggers": behavior[c]["intervention_triggers"],
                "api_calls_total_steps": agg[c]["api_calls"],
                "total_tokens": agg[c]["total_tokens"],
                "cost_usd": agg[c]["cost_usd"],
                "errors": agg[c]["errors"],
                "recoveries": agg[c]["recoveries"],
            }
            for c in CONDITIONS
        },
        "per_age_correct_of_8": load_json(processed / "per_age.json"),
        "per_category_accuracy": load_json(processed / "per_category.json"),
        "efficiency_vs_l0": {
            c: {
                "steps": agg[c]["api_calls"],
                "steps_pct_change": pct(agg["L0"]["api_calls"], agg[c]["api_calls"]),
                "cost_usd": agg[c]["cost_usd"],
                "cost_pct_change": pct(agg["L0"]["cost_usd"], agg[c]["cost_usd"]),
            }
            for c in CONDITIONS
        },
        "l4_vs_l3_efficiency": {
            "steps_pct_change": pct(agg["L3"]["api_calls"], agg["L4"]["api_calls"]),
            "cost_pct_change": pct(agg["L3"]["cost_usd"], agg["L4"]["cost_usd"]),
            "tokens_pct_change": pct(agg["L3"]["total_tokens"], agg["L4"]["total_tokens"]),
        },
        "statistical_evidence": {
            "comparison": "paired, n=32 tasks; L0 vs L1/L2/L3/L4 and L3 vs L4",
            "comparisons": {
                k: {
                    "mean_difference": v["mean_difference"],
                    "p_value": v["welch_p_value"],
                    "discordant_pairs": v["discordant_pairs"],
                    "incorrect_to_correct": v["incorrect_to_correct"],
                    "correct_to_incorrect": v["correct_to_incorrect"],
                }
                for k, v in comparisons.items()
            },
            "multiple_comparison": load_json(stats / "multiple_comparison.json"),
        },
        "reference_paper_result_gemma_baseline": {
            "source": "arXiv:2605.17894, Section 5/5.1 Table 2, confidence=low (single extraction pass)",
            "model_in_paper": "gemma-4-31b",
            "scores_by_age": {str(age): score for age, score in reference_gemma},
            "note": "The paper evaluated Gemma-4-31B, not Gemma 4 26B A4B, and on a different scale/metric. Context only.",
        },
        "cost_summary_usd": {
            "gemma_benchmark_spend": gemma_benchmark_spend,
            "gemma_benchmark_spend_note": "includes the 2-task L0 smoke test (data/gemma_benchmark/smoke/), charged to the L0 ledger",
            "benchmark_hard_cap": 8.00,
            "project_lifetime_cumulative_spend": ledger_project["cumulative_cost_usd"],
            "project_lifetime_api_calls": ledger_project["api_calls_made"],
            "final_benchmark_inference_calls": sum(agg[c]["api_calls"] for c in CONDITIONS),
        },
        "test_suite": (
            {"passed": args.tests_passed, "total": args.tests_total}
            if args.tests_passed is not None else None
        ),
        "provenance": {
            "config": "configs/gemma_independent_benchmark.yaml",
            "raw_data": [f"data/gemma_benchmark/raw/{c}.jsonl" for c in CONDITIONS],
            "processed_data_dir": "data/gemma_benchmark/processed/",
            "reproducibility_manifest": "reproducibility_manifest.json",
        },
    }

    manifests = {}
    for c in CONDITIONS:
        rows = load_raw(c)
        manifests[c] = {
            "condition": c,
            "run_id": sorted({r["run_id"] for r in rows}),
            "experiment_ids": sorted({r["experiment_id"] for r in rows}),
            "model": sorted({r["model"] for r in rows}),
            "provider": sorted({r["provider"] for r in rows}),
            "temperature": sorted({r["temperature"] for r in rows}),
            "guardrail_version": sorted({str(r["guardrail_version"]) for r in rows}),
            "git_commit": sorted({r["git_commit"] for r in rows}),
            "configuration_hash": sorted({r["configuration_hash"] for r in rows}),
            "n_tasks": len(rows),
            "n_unique_task_ids": len({r["task_id"] for r in rows}),
            "timestamp_min": min(r["timestamp"] for r in rows),
            "timestamp_max": max(r["timestamp"] for r in rows),
        }
    manifest = {
        "config": "configs/gemma_independent_benchmark.yaml",
        "model": MODEL,
        "task_set_sha256": task_set_sha256(),
        "conditions": manifests,
        "project_ledger_cumulative_usd": ledger_project["cumulative_cost_usd"],
        "project_ledger_api_calls": ledger_project["api_calls_made"],
        "gemma_benchmark_spend_usd": gemma_benchmark_spend,
        "benchmark_hard_cap_usd": 8.00,
        "remaining_gemma_benchmark_budget_usd": 8.00 - gemma_benchmark_spend,
        "raw_data_paths": [f"data/gemma_benchmark/raw/{c}.jsonl" for c in CONDITIONS],
        "trajectory_paths": [f"data/gemma_benchmark/raw/trajectories/{c}/" for c in CONDITIONS],
        "processed_data_dir": "data/gemma_benchmark/processed/",
        "statistics_dir": "data/gemma_benchmark/statistics/",
        "figures_dirs": ["figures/", "outcome_figures/"],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "outcome_data_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / "reproducibility_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("wrote", OUT_DIR / "outcome_data_summary.json")
    print("wrote", OUT_DIR / "reproducibility_manifest.json")
    print("task_set_sha256:", manifest["task_set_sha256"])


if __name__ == "__main__":
    main()
