"""Append-only JSONL trajectory writer. One line per step, so a run is reproducible and
readable even if it's interrupted mid-episode."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .schema import TrajectoryRecord


@dataclass
class TrajectoryWriter:
    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: TrajectoryRecord) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_json_dict()) + "\n")

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
