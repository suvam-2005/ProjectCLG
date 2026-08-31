import pytest

from childagenteval_research.evaluation.provenance import ProvenanceChain, ProvenanceLink


def test_link_rejects_unknown_stage():
    with pytest.raises(ValueError):
        ProvenanceLink(stage="not_a_real_stage", reference="x")


def test_chain_grounded_in_raw_data():
    chain = ProvenanceChain(links=[
        ProvenanceLink(stage="raw_trajectory", reference="runs/t1/trajectory.jsonl"),
        ProvenanceLink(stage="metric", reference="trajectory_metrics.compute_trajectory_metrics"),
    ])
    assert chain.is_grounded_in_raw_data() is True
    assert chain.is_grounded_in_paper_statement() is False


def test_chain_grounded_in_paper_statement():
    chain = ProvenanceChain(links=[
        ProvenanceLink(stage="paper_statement", reference="arXiv:2605.17894 Table 2"),
    ])
    assert chain.is_grounded_in_paper_statement() is True
    assert chain.is_grounded_in_raw_data() is False


def test_empty_chain_is_grounded_in_nothing():
    chain = ProvenanceChain()
    assert chain.is_grounded_in_raw_data() is False
    assert chain.is_grounded_in_paper_statement() is False
    assert chain.stages_present() == ()
