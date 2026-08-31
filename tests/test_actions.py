import json

import pytest

from childagenteval_research.actions import (
    Action,
    ActionSource,
    ActionValidationError,
    make_recovery_action,
    parse_action,
)


def test_parses_valid_click_action():
    action = parse_action(json.dumps({"action": "click", "target": "btn_1"}))
    assert action.action == "click"
    assert action.target == "btn_1"
    assert action.source == ActionSource.MODEL


def test_parses_valid_type_action():
    action = parse_action(json.dumps({"action": "type", "target": "input_1", "text": "hello"}))
    assert action.text == "hello"


def test_parses_valid_finish_action():
    action = parse_action(json.dumps({"action": "finish"}))
    assert action.action == "finish"


def test_rejects_non_json_text():
    with pytest.raises(ActionValidationError):
        parse_action("I think I should click the button")


def test_rejects_json_that_is_not_an_object():
    with pytest.raises(ActionValidationError):
        parse_action(json.dumps(["click", "btn_1"]))


def test_rejects_bare_json_integer():
    # Regression: observed in the Phase 5C pilot — the model occasionally emits just
    # "5" (or a long degenerate digit string) instead of an action object.
    with pytest.raises(ActionValidationError, match="expected a JSON object, got int"):
        parse_action("5")


def test_rejects_bare_json_string():
    with pytest.raises(ActionValidationError, match="expected a JSON object, got str"):
        parse_action('"5"')


def test_rejects_unknown_action_type():
    with pytest.raises(ActionValidationError):
        parse_action(json.dumps({"action": "teleport", "target": "btn_1"}))


def test_rejects_missing_required_field():
    with pytest.raises(ActionValidationError):
        parse_action(json.dumps({"action": "click"}))  # missing "target"


def test_extra_unknown_fields_are_preserved_in_metadata_not_dropped_silently():
    action = parse_action(json.dumps({"action": "click", "target": "btn_1", "confidence": 0.9}))
    assert action.metadata["confidence"] == 0.9


def test_recovery_action_is_fixed_and_labeled():
    action = make_recovery_action(reason="bad json", raw_model_output="not json")
    assert action.action == "wait"
    assert action.source == ActionSource.MALFORMED_RECOVERY
    assert action.metadata["reason"] == "bad json"
    assert action.metadata["raw_model_output"] == "not json"


def test_action_to_dict_omits_none_and_empty_fields():
    action = Action(action="wait")
    d = action.to_dict()
    assert d == {"action": "wait", "source": "model"}
