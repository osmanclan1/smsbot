"""Tests for intent matching (and precompiled regexes from issue 7)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import intents as intent_module
import messages


def test_where_how_pay():
    intent_id, response = intent_module.match_intent("where do I pay?")
    assert intent_id == "where_how_pay"
    assert response
    assert "oakton.edu" in response
    assert "my.oakton.edu" in response
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


def test_registration_holds():
    intent_id, response = intent_module.match_intent("when does registration open?")
    assert intent_id == "registration_holds"
    assert response and "oakton.edu" in response and "my.oakton" in response
    intent_id2, _ = intent_module.match_intent("I have a hold")
    assert intent_id2 == "registration_holds"


def test_financial_aid():
    intent_id, response = intent_module.match_intent("when does financial aid disburse?")
    assert intent_id == "financial_aid"
    assert response
    intent_id2, _ = intent_module.match_intent("my aid hasn't posted")
    assert intent_id2 == "financial_aid"


def test_contact_human():
    intent_id, response = intent_module.match_intent("who do I call?")
    assert intent_id == "contact_human"
    assert response and "Cashier" in response
    intent_id2, _ = intent_module.match_intent("office hours")
    assert intent_id2 == "contact_human"


def test_already_paid():
    intent_id, response = intent_module.match_intent("I already paid")
    assert intent_id == "already_paid"
    assert response and "post" in response.lower()
    intent_id2, _ = intent_module.match_intent("my payment didn't go through")
    assert intent_id2 == "already_paid"


def test_already_paid_not_where_how_pay():
    intent_id, _ = intent_module.match_intent("I already paid")
    assert intent_id == "already_paid"


def test_what_is_oakton_alert():
    intent_id, response = intent_module.match_intent("what is Oakton Alert?")
    assert intent_id == "what_is_oakton_alert"
    assert response and "tuition reminders" in response
    intent_id2, _ = intent_module.match_intent("why am I getting this")
    assert intent_id2 == "what_is_oakton_alert"


def test_myoakton_login():
    intent_id, response = intent_module.match_intent("I can't log in")
    assert intent_id == "myoakton_login"
    assert response and "my.oakton" in response
    intent_id2, _ = intent_module.match_intent("forgot password")
    assert intent_id2 == "myoakton_login"
