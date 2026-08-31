"""Machine-readable source/evidence table (brief §2). Every experimental fact used
anywhere in this project's documentation must have a row here. Confidence reflects how
the fact was actually verified — not how important it is.

Extraction method note: facts below were obtained via automated fetch-and-summarize
tooling (WebFetch) over the paper's arXiv HTML/PDF and the GitHub repository — this is
itself a secondary transformation of the primary source, not a human reading of the PDF.
Where a fact was independently reproduced by two differently-worded extraction passes,
confidence is HIGH. Where only one pass produced it, confidence is at most MEDIUM. Where
a pass produced internally implausible values (see the Qwen3.5-27B factor-z-score
anomaly, `notes` below), confidence is LOW regardless of how precise the numbers looked.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvidenceConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNAVAILABLE = "unavailable"


class EvidenceStatus(str, Enum):
    CONFIRMED = "confirmed"
    UNVERIFIED_SINGLE_PASS = "unverified_single_pass"
    EXTRACTION_RELIABILITY_CONCERN = "extraction_reliability_concern"
    UNAVAILABLE = "unavailable"
    REQUIRES_AUTHOR_ACCESS = "requires_author_access"


@dataclass(frozen=True)
class SourceEvidence:
    claim: str
    source: str
    location: str
    confidence: EvidenceConfidence
    status: EvidenceStatus
    notes: str | None = None


EVIDENCE_TABLE: tuple[SourceEvidence, ...] = (
    SourceEvidence(
        claim="Paper title is 'Evaluating Cognitive Age Alignment in Interactive AI Agents', "
              "authors Yifan Shen, Jiawen Zhang, Jian Xu, Junho Kim, Ismini Lourentzou, Xu Cao, Meihuan Huang",
        source="arXiv:2605.17894", location="Abstract/header",
        confidence=EvidenceConfidence.HIGH, status=EvidenceStatus.CONFIRMED,
        notes="Consistent across 3 independent fetches (Phase 0 x2, Phase 4 x1) and arXiv search results.",
    ),
    SourceEvidence(
        claim="ChildAgentEval is inspired by the Wechsler Intelligence Scale for Children (WISC)",
        source="arXiv:2605.17894 + GitHub repo README", location="Abstract; docs/benchmark_overview.md",
        confidence=EvidenceConfidence.HIGH, status=EvidenceStatus.CONFIRMED,
    ),
    SourceEvidence(
        claim="Ten interactive subtests: Block Design(T1), Similarities(T2), Digit Span(T3), "
              "Picture Concepts(T4), Coding(T5), Vocabulary(T6), Letter-Number Sequencing(T7), "
              "Matrix Reasoning(T8), Comprehension(T9), Symbol Search(T10)",
        source="arXiv:2605.17894 HTML", location="Section describing benchmark design",
        confidence=EvidenceConfidence.HIGH, status=EvidenceStatus.CONFIRMED,
        notes="Consistent across 2 independent fetches (Phase 0, Phase 4).",
    ),
    SourceEvidence(
        claim="Baseline anchor ages: 7, 10, 13, 16. Skill-guided age bands: 6-8, 9-11, 12-14, 15-17",
        source="arXiv:2605.17894 HTML", location="Methodology section",
        confidence=EvidenceConfidence.HIGH, status=EvidenceStatus.CONFIRMED,
        notes="Consistent across 3 independent fetches.",
    ),
    SourceEvidence(
        claim="Models evaluated: proprietary GPT-5.4, Gemini-3.1-Pro, Gemini-3.1-Flash-Lite, "
              "Qwen-3.6-Plus; open-weight Qwen-3.5-27B, Gemma-4-31B",
        source="arXiv:2605.17894 HTML", location="Experiments section (model list)",
        confidence=EvidenceConfidence.HIGH, status=EvidenceStatus.CONFIRMED,
        notes="Consistent across 2 independent fetches (Phase 0, Phase 4). No parameter counts, "
              "exact checkpoint dates, or version hashes were reported for any model.",
    ),
    SourceEvidence(
        claim="Environment is Playwright-driven; DOM-assisted mode provides a screenshot plus a "
              "sanitized accessibility tree of visible interactive elements",
        source="arXiv:2605.17894 HTML", location="Environment/methodology section",
        confidence=EvidenceConfidence.HIGH, status=EvidenceStatus.CONFIRMED,
    ),
    SourceEvidence(
        claim="Objective subtests use strict binary scoring; Coding uses correct-operations-in-time-limit; "
              "open-ended verbal subtests use a 0/1/2-point rubric scored by two independent human raters "
              "blind to model identity/condition/age/hypothesis",
        source="arXiv:2605.17894 HTML", location="Scoring/methodology section",
        confidence=EvidenceConfidence.MEDIUM, status=EvidenceStatus.UNVERIFIED_SINGLE_PASS,
        notes="Reported once (Phase 0 fetch); not independently re-confirmed in Phase 4's pass, "
              "which focused on numeric results instead.",
    ),
    SourceEvidence(
        claim="A complete administration requires approximately one hour of wall-clock time",
        source="arXiv:2605.17894 HTML", location="Appendix (administration procedure)",
        confidence=EvidenceConfidence.MEDIUM, status=EvidenceStatus.UNVERIFIED_SINGLE_PASS,
        notes="Reported consistently in Phase 0 and Phase 4 fetches, but both derive from the same "
              "automated extraction tool over the same source, not independent human verification.",
    ),
    SourceEvidence(
        claim="Calibration corpus for skill distillation draws on CHILDES, OCSC, Frog Story, LCCPW, ClassBank",
        source="arXiv:2605.17894 HTML", location="Skill-distillation methodology section",
        confidence=EvidenceConfidence.MEDIUM, status=EvidenceStatus.UNVERIFIED_SINGLE_PASS,
    ),
    SourceEvidence(
        claim="Qwen3.5-27B baseline Total/Overall composite score: 0.32 (age 7), 0.34 (age 10), "
              "0.29 (age 13), 0.30 (age 16)",
        source="arXiv:2605.17894 HTML, Table 2 ('Open-Source Models')",
        location="Section 5 / 5.1, Table 2",
        confidence=EvidenceConfidence.MEDIUM, status=EvidenceStatus.CONFIRMED,
        notes="These four numbers were reproduced identically across two independently-worded "
              "extraction passes (Phase 4), which is why confidence is MEDIUM rather than LOW. Still "
              "not verified against a human reading of the actual table, since automated PDF/HTML "
              "table extraction is known-unreliable (see the next row).",
    ),
    SourceEvidence(
        claim="Qwen3.5-27B per-factor z-scores and per-subtest (T1-T10) breakdown from the same Table 2",
        source="arXiv:2605.17894 HTML, Table 2", location="Section 5.1, Table 2 (granular columns)",
        confidence=EvidenceConfidence.LOW, status=EvidenceStatus.EXTRACTION_RELIABILITY_CONCERN,
        notes="REJECTED for use: the single extraction pass that produced this granular table reported "
              "FSIQ z-scores of +4.5 to +5.3 SD for a model whose own Overall/Total score (0.32) is "
              "reported as one of the lowest of any model tested - an internal contradiction indicating "
              "the automated table-to-markdown conversion likely misaligned columns/rows. Not included "
              "in reference_results.json. Requires a human reading of the actual PDF table (or author "
              "access) before any per-subtest or per-factor number from this paper is used.",
    ),
    SourceEvidence(
        claim="Qwen3.5-27B skill-guided Total scores: 0.23 (6-8), 0.23 (9-11), 0.24 (12-14), 0.28 (15-17)",
        source="arXiv:2605.17894 HTML, Table 2", location="Section 5.1, Table 2",
        confidence=EvidenceConfidence.LOW, status=EvidenceStatus.EXTRACTION_RELIABILITY_CONCERN,
        notes="Single-pass extraction from the same table flagged above as unreliable. Not included in "
              "reference_results.json pending verification.",
    ),
    SourceEvidence(
        claim="GPT-5.4 baseline age-vs-score Spearman rho = -0.40; GPT-5.4 skill-guided rho = 1.00",
        source="arXiv:2605.17894 HTML", location="Section 5.2 / Figure 5 discussion",
        confidence=EvidenceConfidence.LOW, status=EvidenceStatus.UNVERIFIED_SINGLE_PASS,
        notes="Single-pass extraction, not cross-checked. Not included in reference_results.json.",
    ),
    SourceEvidence(
        claim="Linguistic complexity composite (GPT-5.4 agent): 0.09 (age 7), 0.38 (age 16)",
        source="arXiv:2605.17894 HTML", location="Appendix B.2",
        confidence=EvidenceConfidence.LOW, status=EvidenceStatus.UNVERIFIED_SINGLE_PASS,
        notes="Single-pass extraction, not cross-checked. Not included in reference_results.json.",
    ),
    SourceEvidence(
        claim="The paper's own evaluation framework does not compute confidence intervals, formal "
              "significance tests, or variance estimates",
        source="arXiv:2605.17894 HTML", location="Appendix A.5 (quoted)",
        confidence=EvidenceConfidence.MEDIUM, status=EvidenceStatus.UNVERIFIED_SINGLE_PASS,
        notes="Presented as a direct quote by the extraction tool; not independently re-verified, but "
              "highly consequential (see docs/phase4_reproduction_specification.md limitations) so "
              "flagged prominently rather than silently trusted.",
    ),
    SourceEvidence(
        claim="Total participant/trial counts and inter-rater reliability statistics (e.g. Cohen's "
              "kappa) are not reported anywhere in the paper",
        source="arXiv:2605.17894 HTML", location="Whole-document search (absence)",
        confidence=EvidenceConfidence.MEDIUM, status=EvidenceStatus.UNAVAILABLE,
        notes="An absence claim from automated full-text search is inherently less certain than a "
              "positive claim; flagged for confirmation via author access.",
    ),
    SourceEvidence(
        claim="Official GitHub repository contains no benchmark implementation, task definitions, "
              "scoring code, or data - only README, CITATION files, and two docs pages",
        source="GitHub PediaMedAI/ChildAgentEval", location="Repository file tree (API-verified)",
        confidence=EvidenceConfidence.HIGH, status=EvidenceStatus.CONFIRMED,
        notes="Verified directly via the GitHub REST API tree listing in Phase 0, not summarized.",
    ),
    SourceEvidence(
        claim="Full evaluation protocol, item content, and scoring rubrics are withheld due to WISC "
              "copyright; evaluation is administered by the authors on request via email",
        source="GitHub repo docs/evaluation_access.md", location="Full file, fetched verbatim",
        confidence=EvidenceConfidence.HIGH, status=EvidenceStatus.CONFIRMED,
        notes="Fetched and quoted verbatim in Phase 0 - not a summary.",
    ),
    SourceEvidence(
        claim="qwen/qwen3.5-27b is a live, listed OpenRouter model (262K context, vision-language)",
        source="OpenRouter public /models API", location="Live API response",
        confidence=EvidenceConfidence.HIGH, status=EvidenceStatus.CONFIRMED,
        notes="Verified directly against the API in Phase 0/1, not summarized.",
    ),
)
