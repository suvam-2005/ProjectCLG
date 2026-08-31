"""Future expected-vs-actual report template (brief §14). The `possible_explanations`
section is structurally forbidden from containing a bare OBSERVATION — an explanation is
always an INTERPRETATION or a HYPOTHESIS, never presented as established fact.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class StatementKind(str, Enum):
    OBSERVATION = "observation"       # a directly measured fact
    INTERPRETATION = "interpretation"  # a reasoned reading of observations
    HYPOTHESIS = "hypothesis"          # an untested speculative explanation


@dataclass(frozen=True)
class TaggedStatement:
    kind: StatementKind
    text: str

    def render(self) -> str:
        return f"[{self.kind.value.upper()}] {self.text}"


@dataclass
class ExpectedVsActualReport:
    title: str
    what_paper_reported: list[TaggedStatement] = field(default_factory=list)
    what_we_observed: list[TaggedStatement] = field(default_factory=list)
    difference: list[TaggedStatement] = field(default_factory=list)
    statistical_evidence: list[TaggedStatement] = field(default_factory=list)
    possible_explanations: list[TaggedStatement] = field(default_factory=list)
    limitations: list[TaggedStatement] = field(default_factory=list)

    def __post_init__(self) -> None:
        for statement in self.possible_explanations:
            if statement.kind == StatementKind.OBSERVATION:
                raise ValueError(
                    "possible_explanations must never contain a bare OBSERVATION — "
                    "an explanation is an INTERPRETATION or a HYPOTHESIS by definition"
                )

    def render_markdown(self) -> str:
        def section(name: str, statements: list[TaggedStatement]) -> str:
            body = "\n".join(f"- {s.render()}" for s in statements) if statements else "- (none yet)"
            return f"## {name}\n\n{body}\n"

        return "\n".join(
            [
                f"# {self.title}",
                "",
                section("What the reference paper expected/reported", self.what_paper_reported),
                section("What our reproduction actually produced", self.what_we_observed),
                section("Difference", self.difference),
                section("Statistical evidence", self.statistical_evidence),
                section("Possible explanations", self.possible_explanations),
                section("Limitations", self.limitations),
            ]
        )
