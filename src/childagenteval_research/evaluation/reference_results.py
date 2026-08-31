"""REFERENCE_RESULT schema and loader. Every row traces to a source/location and
carries the confidence/status classification from source_evidence.py — this module
never invents a value; it only loads what reference/reference_results.json contains.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .result_kind import ResultKind


@dataclass(frozen=True)
class ReferenceResult:
    result_kind: str
    metric: str
    model: str
    condition: str
    value: float
    source: str
    location: str
    confidence: str
    status: str
    target_age: int | None = None
    age_band: str | None = None
    subtest: str | None = None
    uncertainty: float | None = None
    n: int | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.result_kind != ResultKind.REFERENCE_RESULT.value:
            raise ValueError("ReferenceResult.result_kind must be 'reference_result' — never mix categories")
        if self.target_age is not None and self.age_band is not None:
            raise ValueError(f"{self.metric!r} row sets both target_age and age_band — these must not be mixed")


def load_reference_results(path: Path) -> list[ReferenceResult]:
    raw: list[dict[str, Any]] = json.loads(path.read_text())
    return [ReferenceResult(**row) for row in raw]
