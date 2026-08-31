from childagenteval_research.evaluation.result_kind import ResultKind


def test_four_result_kinds_never_overlap_in_value():
    values = [k.value for k in ResultKind]
    assert len(values) == len(set(values)) == 4


def test_reference_result_is_distinct_from_our_result():
    assert ResultKind.REFERENCE_RESULT != ResultKind.OUR_RESULT
    assert ResultKind.REPRODUCTION_RESULT != ResultKind.GUARDRAIL_RESULT
