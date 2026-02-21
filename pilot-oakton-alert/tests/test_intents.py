"""Tests for intent matching (and precompiled regexes from issue 7)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import intents as intent_module
import messages


def test_where_how_pay():
    intent_id, response = intent_module.match_intent("where do I pay?")
    assert intent_id == "where_how_pay"
    assert "my.oakton.edu" in (response or "")
    intent_id2, _ = intent_module.match_intent("payment link")
    assert intent_id2 == "where_how_pay"


def test_balance():
    intent_id, response = intent_module.match_intent("what do I owe?")
    assert intent_id == "balance_how_much"
    assert response


def test_when_deadline():
    intent_id, _ = intent_module.match_intent("when is the deadline?")
    assert intent_id == "when_deadline"


def test_withdraw():
    intent_id, _ = intent_module.match_intent("how do I withdraw")
    assert intent_id == "withdraw_drop_safe_removal"


def test_other_fallback():
    intent_id, response = intent_module.match_intent("random gibberish xyz")
    assert intent_id == "other"
    assert response is None


def test_get_response_for_message_uses_fallback():
    out = intent_module.get_response_for_message("random gibberish")
    assert out == messages.FALLBACK_RESPONSE


def test_empty_message():
    intent_id, response = intent_module.match_intent("")
    assert intent_id == "other"
    assert response is None
