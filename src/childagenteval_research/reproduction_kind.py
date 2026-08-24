"""Enforces the OFFICIAL_REPRODUCTION vs INDEPENDENT_EXPERIMENT distinction everywhere
in code and telemetry, so the two are never accidentally conflated.

OFFICIAL_REPRODUCTION: results produced against the actual ChildAgentEval benchmark, as
administered by the paper's authors. Currently BLOCKED — see docs/phase0_findings.md.

INDEPENDENT_EXPERIMENT: anything produced by this codebase's own environments (e.g.
MockEnvironment, the generic Playwright adapter against non-ChildAgentEval pages). Never
to be reported or described as a ChildAgentEval result.
"""
from __future__ import annotations

from enum import Enum


class ReproductionKind(str, Enum):
    OFFICIAL_REPRODUCTION = "OFFICIAL_REPRODUCTION"
    INDEPENDENT_EXPERIMENT = "INDEPENDENT_EXPERIMENT"


OFFICIAL_REPRODUCTION_STATUS = (
    "BLOCKED — official ChildAgentEval benchmark access has not been granted. "
    "See docs/phase0_findings.md and docs/email_draft_to_authors.md."
)

ENVIRONMENT_ADAPTER_KIND: dict[str, ReproductionKind] = {
    "official_childagenteval": ReproductionKind.OFFICIAL_REPRODUCTION,
    "mock": ReproductionKind.INDEPENDENT_EXPERIMENT,
    "playwright_generic": ReproductionKind.INDEPENDENT_EXPERIMENT,
}


def classify_adapter(adapter: str) -> ReproductionKind:
    try:
        return ENVIRONMENT_ADAPTER_KIND[adapter]
    except KeyError:
        raise ValueError(f"unregistered environment adapter {adapter!r}; add it to ENVIRONMENT_ADAPTER_KIND") from None
