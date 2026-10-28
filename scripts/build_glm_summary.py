"""Builds reports/glm/outcome_data_summary.json and reports/glm/reproducibility_manifest.json
for the GLM 5.3 Flash run (L0-L4). Every field is read from data/glm_benchmark/ and the
.state/glm/ ledgers — nothing hand-typed. The reference paper has no GLM result; the
summary carries the cross-model L0 comparison against OUR Qwen, Gemma and DeepSeek runs
instead, plus the reasoning-token measurements (GLM 5.3 Flash cannot disable reasoning).

Usage: python scripts/build_glm_summary.py [--tests-passed N --tests-total N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "glm_benchmark"
OUT_DIR = PROJECT_ROOT / "reports" / "glm"
CONDITIONS = ["L0", "L1", "L2", "L3", "L4"]
MODEL = "z-ai/glm-5.3-flash"


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

    ledger_project = load_json(PROJECT_ROOT / ".state" / "cost_ledger.json")
    ledger_by_condition = {c: load_json(PROJECT_ROOT / ".state" / "glm" / f"benchmark_cost_ledger_{c}.json") for c in CONDITIONS}
    glm_benchmark_spend = sum(l["cumulative_cost_usd"] for l in ledger_by_condition.values())

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
        "reference_paper_result": None,
        "reference_note": "The reference paper (arXiv:2605.17894) did not evaluate any GLM model.",
        "l0_accuracy_by_age_across_models": load_json(processed / "reference_comparison.json"),
        "reasoning": {
            "setting": {"effort": "minimal"},
            "note": ("GLM 5.3 Flash rejects reasoning {enabled: false}; this run used the lowest setting. "
                     "The Qwen, Gemma and DeepSeek runs used reasoning disabled."),
            "by_condition": load_json(processed / "reasoning.json"),
        },
        "cost_summary_usd": {
            "glm_benchmark_spend": glm_benchmark_spend,
            "glm_benchmark_spend_note": "includes the 2-task L0 smoke test (data/glm_benchmark/smoke/), charged to the L0 ledger",
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
            "config": "configs/glm_independent_benchmark.yaml",
            "raw_data": [f"data/glm_benchmark/raw/{c}.jsonl" for c in CONDITIONS],
            "processed_data_dir": "data/glm_benchmark/processed/",
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
        "config": "configs/glm_independent_benchmark.yaml",
        "model": MODEL,
        "task_set_sha256": task_set_sha256(),
        "conditions": manifests,
        "project_ledger_cumulative_usd": ledger_project["cumulative_cost_usd"],
        "project_ledger_api_calls": ledger_project["api_calls_made"],
        "glm_benchmark_spend_usd": glm_benchmark_spend,
        "benchmark_hard_cap_usd": 8.00,
        "remaining_glm_benchmark_budget_usd": 8.00 - glm_benchmark_spend,
        "raw_data_paths": [f"data/glm_benchmark/raw/{c}.jsonl" for c in CONDITIONS],
        "trajectory_paths": [f"data/glm_benchmark/raw/trajectories/{c}/" for c in CONDITIONS],
        "processed_data_dir": "data/glm_benchmark/processed/",
        "statistics_dir": "data/glm_benchmark/statistics/",
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
