"""Trajectory-shape metrics, independent of benchmark-specific scoring. Operates on the
same dict shape TrajectoryWriter.read_all() / TrajectoryRecord.to_json_dict() produce
(see telemetry/schema.py), so it works on both live and replayed trajectories.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass
class TrajectoryMetrics:
    n: int
    total_steps: int
    successful_steps: int
    failed_steps: int
    recovery_steps: int
    repeated_actions: int
    unnecessary_actions: int | None  # requires benchmark-specific optimal-path knowledge; always None for now
    page_revisits: int | None
    action_diversity: float | None
    trajectory_length: int
    completion_time_s: float | None
    mean_action_latency_s: float | None
    mean_observation_to_action_latency_s: float | None


def _final_action_key(record: Mapping[str, Any]) -> tuple[Any, Any]:
    final = record.get("action", {}).get("final", {})
    return final.get("action"), final.get("target")


def compute_trajectory_metrics(records: Sequence[Mapping[str, Any]]) -> TrajectoryMetrics:
    n = len(records)
    successful = sum(1 for r in records if r.get("action_result", {}).get("success") is True)
    failed = sum(1 for r in records if r.get("action_result", {}).get("success") is False)
    recovered = sum(1 for r in records if r.get("recovery") is not None)

    action_keys = [_final_action_key(r) for r in records]
    repeated = sum(1 for i in range(1, n) if action_keys[i] == action_keys[i - 1])
    distinct_actions = len({a for a, _ in action_keys}) if action_keys else 0
    action_diversity = (distinct_actions / n) if n else None

    urls = [
        r.get("observation_metadata", {}).get("page_metadata", {}).get("url")
        for r in records
    ]
    known_urls = [u for u in urls if u is not None]
    page_revisits: int | None = None
    if known_urls:
        seen: set[Any] = set()
        page_revisits = 0
        for u in known_urls:
            if u in seen:
                page_revisits += 1
            seen.add(u)

    completion_time_s = None
    if n >= 2:
        completion_time_s = records[-1]["timestamp"] - records[0]["timestamp"]

    latencies = [r["latency_s"] for r in records if r.get("latency_s") is not None]
    mean_latency = statistics.mean(latencies) if latencies else None

    return TrajectoryMetrics(
        n=n,
        total_steps=n,
        successful_steps=successful,
        failed_steps=failed,
        recovery_steps=recovered,
        repeated_actions=repeated,
        unnecessary_actions=None,
        page_revisits=page_revisits,
        action_diversity=action_diversity,
        trajectory_length=n,
        completion_time_s=completion_time_s,
        # This project does not separately time environment step execution today, so
        # "action latency" and "observation-to-action latency" both currently resolve to
        # the same measured quantity: model decision latency (TrajectoryRecord.latency_s).
        mean_action_latency_s=mean_latency,
        mean_observation_to_action_latency_s=mean_latency,
    )
