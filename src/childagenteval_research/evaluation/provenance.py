"""Data provenance chain (brief §13): raw_trajectory -> task_result -> processed_result
-> metric -> statistical_analysis -> figure_or_table -> paper_statement. Enforces that
no OUR_RESULT/REPRODUCTION_RESULT/GUARDRAIL_RESULT figure or table can be built without
a chain reaching back to a raw trajectory reference — no manually typed numbers.
"""
from __future__ import annotations

from dataclasses import dataclass, field

STAGES: tuple[str, ...] = (
    "raw_trajectory",
    "task_result",
    "processed_result",
    "metric",
    "statistical_analysis",
    "figure_or_table",
    "paper_statement",
)


@dataclass(frozen=True)
class ProvenanceLink:
    stage: str
    reference: str  # a path, run_id, experiment_id, or citation identifying this artifact

    def __post_init__(self) -> None:
        if self.stage not in STAGES:
            raise ValueError(f"unknown provenance stage {self.stage!r}; must be one of {STAGES}")


@dataclass
class ProvenanceChain:
    links: list[ProvenanceLink] = field(default_factory=list)

    def stages_present(self) -> tuple[str, ...]:
        return tuple(link.stage for link in self.links)

    def reaches(self, stage: str) -> bool:
        return stage in self.stages_present()

    def is_grounded_in_raw_data(self) -> bool:
        """A chain for anything claiming to be OUR_RESULT/REPRODUCTION_RESULT/
        GUARDRAIL_RESULT must reach back to a raw trajectory — this is what "no
        manually typed experimental results" means operationally."""
        return self.reaches("raw_trajectory")

    def is_grounded_in_paper_statement(self) -> bool:
        """A REFERENCE_RESULT's chain instead terminates at a cited paper statement."""
        return self.reaches("paper_statement")
