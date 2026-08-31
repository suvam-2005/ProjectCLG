from pathlib import Path

import pytest

from childagenteval_research.evaluation.reference_results import ReferenceResult, load_reference_results
from childagenteval_research.evaluation.result_kind import ResultKind
from childagenteval_research.evaluation.source_evidence import EVIDENCE_TABLE, EvidenceConfidence, EvidenceStatus

REFERENCE_RESULTS_PATH = Path(__file__).parent.parent / "reference" / "reference_results.json"


def test_reference_result_rejects_wrong_result_kind():
    with pytest.raises(ValueError):
        ReferenceResult(
            result_kind="our_result", metric="x", model="m", condition="baseline",
            value=0.5, source="s", location="l", confidence="low", status="unverified_single_pass",
        )


def test_reference_result_rejects_mixed_age_representation():
    with pytest.raises(ValueError):
        ReferenceResult(
            result_kind=ResultKind.REFERENCE_RESULT.value, metric="x", model="m", condition="baseline",
            value=0.5, source="s", location="l", confidence="low", status="unverified_single_pass",
            target_age=7, age_band="6-8",
        )


def test_load_real_reference_results_file():
    results = load_reference_results(REFERENCE_RESULTS_PATH)
    assert len(results) > 0
    assert all(r.result_kind == "reference_result" for r in results)


def test_qwen_baseline_rows_are_confirmed_medium_confidence():
    results = load_reference_results(REFERENCE_RESULTS_PATH)
    qwen_baseline = [
        r for r in results
        if r.model == "qwen3.5-27b" and r.condition == "baseline" and r.metric == "total_composite_score"
    ]
    assert len(qwen_baseline) == 4
    assert {r.target_age for r in qwen_baseline} == {7, 10, 13, 16}
    assert all(r.confidence == "medium" and r.status == "confirmed" for r in qwen_baseline)


def test_low_confidence_rows_are_explicitly_flagged_not_silently_included():
    results = load_reference_results(REFERENCE_RESULTS_PATH)
    low_confidence = [r for r in results if r.confidence == "low"]
    assert len(low_confidence) > 0
    assert all(r.status != "confirmed" for r in low_confidence)


def test_evidence_table_every_row_has_source_and_location():
    assert len(EVIDENCE_TABLE) > 0
    for row in EVIDENCE_TABLE:
        assert row.claim
        assert row.source
        assert row.location
        assert isinstance(row.confidence, EvidenceConfidence)
        assert isinstance(row.status, EvidenceStatus)


def test_evidence_table_flags_the_rejected_granular_table():
    rejected = [r for r in EVIDENCE_TABLE if r.status == EvidenceStatus.EXTRACTION_RELIABILITY_CONCERN]
    assert len(rejected) >= 1
    assert any("factor" in r.claim.lower() or "subtest" in r.claim.lower() for r in rejected)
