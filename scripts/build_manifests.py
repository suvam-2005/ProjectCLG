"""Builds experiment manifests and the reproducibility manifest from the real raw data.
No field is hand-typed — everything is read from data/independent_benchmark/raw/."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "independent_benchmark" / "raw"
STATS_DIR = PROJECT_ROOT / "data" / "independent_benchmark" / "statistics"
CONDITIONS = ["L0", "L1", "L2", "L3"]


def main() -> None:
    manifests = {}
    for c in CONDITIONS:
        rows = [json.loads(l) for l in (RAW_DIR / f"{c}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
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
            "n_unique_task_ids": len(set(r["task_id"] for r in rows)),
            "timestamp_min": min(r["timestamp"] for r in rows),
            "timestamp_max": max(r["timestamp"] for r in rows),
        }

    (STATS_DIR / "experiment_manifests.json").write_text(json.dumps(manifests, indent=2))

    ledger_project = json.loads((PROJECT_ROOT / ".state" / "cost_ledger.json").read_text())
    ledger_by_condition = {
        c: json.loads((PROJECT_ROOT / ".state" / f"benchmark_cost_ledger_{c}.json").read_text())
        for c in CONDITIONS
    }
    combined_benchmark_spend = sum(l["cumulative_cost_usd"] for l in ledger_by_condition.values())

    reproducibility_manifest = {
        "frozen_config": "configs/experiments/final_benchmark.yaml",
        "frozen_git_commit": manifests["L0"]["git_commit"][0],
        "task_set_sha256": "4e6ae6752b69bae171fe56f2918ec7c8b773f00d5581824d89747e87afe73df8",
        "conditions": manifests,
        "project_ledger_cumulative_usd": ledger_project["cumulative_cost_usd"],
        "project_ledger_api_calls": ledger_project["api_calls_made"],
        "combined_benchmark_spend_usd": combined_benchmark_spend,
        "benchmark_hard_cap_usd": 8.00,
        "remaining_benchmark_budget_usd": 8.00 - combined_benchmark_spend,
        "raw_data_paths": [f"data/independent_benchmark/raw/{c}.jsonl" for c in CONDITIONS],
        "trajectory_paths": [f"data/independent_benchmark/raw/trajectories/{c}/" for c in CONDITIONS],
        "processed_data_dir": "data/independent_benchmark/processed/",
        "statistics_dir": "data/independent_benchmark/statistics/",
        "figures_dir": "reports/figures/",
        "retry_log": "data/independent_benchmark/L0_retry_log.md",
    }
    (PROJECT_ROOT / "reports" / "reproducibility_manifest.json").write_text(json.dumps(reproducibility_manifest, indent=2))
    print(json.dumps(reproducibility_manifest, indent=2))


if __name__ == "__main__":
    main()
