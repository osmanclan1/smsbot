"""Tests for SMS webhook (in-memory behavior, normalized phone for rate limit)."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _webhook_body(from_number: str, text: str, message_id: str = "msg-id-123"):
    return {
        "data": {
            "payload": {
                "id": message_id,
                "from": {"phone_number": from_number},
                "text": text,
                "messaging_profile_id": None,
            }
        }
    }


@patch("webhook.sms_client.send_sms")
def test_webhook_help_returns_200(mock_send):
    mock_send.return_value = {"success": True, "message_id": "m1", "error": None}
    r = client.post(
        "/api/sms/webhook",
        json=_webhook_body("+15551111111", "help", "id-help-1"),
    )
    assert r.status_code == 200
    assert r.json() == {}
    mock_send.assert_called_once()
    assert "help" in mock_send.call_args[0][1].lower() or "oaktonalert" in mock_send.call_args[0][1].lower()


@patch("webhook.sms_client.send_sms")
def test_webhook_opt_out_then_opted_out_reply(mock_send):
    import storage
    mock_send.return_value = {"success": True, "message_id": "m2", "error": None}
    phone = "+15552222221"
    storage.opt_in(phone)  # ensure not opted out initially
    try:
        r = client.post(
            "/api/sms/webhook",
            json=_webhook_body(phone, "stop", "id-stop-1"),
        )
        assert r.status_code == 200
        assert storage.is_opted_out(phone) is True
        mock_send.assert_called_once()
    finally:
        storage.opt_in(phone)


@patch("webhook.sms_client.send_sms")
def test_webhook_duplicate_message_id_processed_once(mock_send):
    mock_send.return_value = {"success": True, "message_id": "m3", "error": None}
    body = _webhook_body("+15553333331", "help", "id-dup-1")
    r1 = client.post("/api/sms/webhook", json=body)
    r2 = client.post("/api/sms/webhook", json=body)
    assert r1.status_code == 200
    assert r2.status_code == 200
    # First call triggers send_sms; second is duplicate so no extra send
    assert mock_send.call_count == 1


@patch("webhook.sms_client.send_sms")
def test_webhook_intent_gets_canned_response(mock_send):
    mock_send.return_value = {"success": True, "message_id": "m4", "error": None}
    r = client.post(
        "/api/sms/webhook",
        json=_webhook_body("+15554444441", "where do I pay?", "id-intent-1"),
    )
    assert r.status_code == 200
    mock_send.assert_called_once()
    text_sent = mock_send.call_args[0][1]
    assert "oakton.edu" in text_sent and (
        "my.oakton.edu" in text_sent or "pay" in text_sent.lower()
    )
