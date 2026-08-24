import pytest

from childagenteval_research.evaluation.ablation import IMPLEMENTED_ABLATIONS, R3AblationVariant
from childagenteval_research.evaluation.age_conditions import (
    BASELINE_ANCHOR_AGES,
    SKILL_GUIDED_AGE_BANDS,
    AgeConditionMismatchError,
    validate_age_band,
    validate_anchor_age,
)
from childagenteval_research.evaluation.conditions import (
    IMPLEMENTED_CONDITIONS,
    STANDARD_COMPARISONS,
    ResearchCondition,
)


def test_four_research_conditions_exist():
    assert {c.name for c in ResearchCondition} == {
        "R0_ORIGINAL_BASELINE", "R1_OUTPUT_GUARDRAIL", "R2_ACTION_GUARDRAIL", "R3_DYNAMIC_GUARDRAIL",
    }


def test_only_r0_is_implemented():
    assert IMPLEMENTED_CONDITIONS == frozenset({ResearchCondition.R0_ORIGINAL_BASELINE})


def test_standard_comparisons_cover_r0_vs_each_and_chain():
    pairs = set(STANDARD_COMPARISONS)
    assert (ResearchCondition.R0_ORIGINAL_BASELINE, ResearchCondition.R1_OUTPUT_GUARDRAIL) in pairs
    assert (ResearchCondition.R0_ORIGINAL_BASELINE, ResearchCondition.R2_ACTION_GUARDRAIL) in pairs
    assert (ResearchCondition.R0_ORIGINAL_BASELINE, ResearchCondition.R3_DYNAMIC_GUARDRAIL) in pairs
    assert (ResearchCondition.R1_OUTPUT_GUARDRAIL, ResearchCondition.R2_ACTION_GUARDRAIL) in pairs
    assert (ResearchCondition.R2_ACTION_GUARDRAIL, ResearchCondition.R3_DYNAMIC_GUARDRAIL) in pairs


def test_baseline_anchor_ages_match_paper():
    assert BASELINE_ANCHOR_AGES == (7, 10, 13, 16)


def test_skill_guided_age_bands_match_paper():
    assert SKILL_GUIDED_AGE_BANDS == ("6-8", "9-11", "12-14", "15-17")


def test_validate_anchor_age_rejects_invented_age():
    validate_anchor_age(10)  # does not raise
    with pytest.raises(AgeConditionMismatchError):
        validate_anchor_age(11)


def test_validate_age_band_rejects_invented_band():
    validate_age_band("9-11")  # does not raise
    with pytest.raises(AgeConditionMismatchError):
        validate_age_band("7")  # an anchor age is not a valid band


def test_r3_ablation_variants_defined_but_none_implemented():
    assert R3AblationVariant.FULL.value == "full_dynamic_guardrail"
    assert len(list(R3AblationVariant)) == 6
    assert IMPLEMENTED_ABLATIONS == frozenset()
