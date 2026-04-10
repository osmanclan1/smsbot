"""Tests for trigger API (in-memory opt-out respected)."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@patch("trigger.sms_client.send_sms")
def test_trigger_success(mock_send):
    mock_send.return_value = {"success": True, "message_id": "msg-123", "error": None}
    r = client.post(
        "/api/trigger",
        json={"phone_number": "+15551234567", "trigger_type": "registration_opens"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["skipped"] is False
    assert data["message_id"] == "msg-123"
    mock_send.assert_called_once()


@patch("trigger.sms_client.send_sms")
def test_trigger_skipped_when_opted_out(mock_send):
    import storage
    storage.opt_out("+15559876543")
    try:
        r = client.post(
            "/api/trigger",
            json={"phone_number": "+15559876543", "trigger_type": "registration_opens"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is False
        assert data["skipped"] is True
        assert data["reason"] == "opted_out"
        mock_send.assert_not_called()
    finally:
        storage.opt_in("+15559876543")


def test_trigger_unknown_type_400():
    r = client.post(
        "/api/trigger",
        json={"phone_number": "+15551234567", "trigger_type": "unknown_type"},
    )
    assert r.status_code == 400


@patch("trigger.sms_client.send_sms")
def test_trigger_payment_reminder_with_days(mock_send):
    mock_send.return_value = {"success": True, "message_id": "msg-456", "error": None}
    r = client.post(
        "/api/trigger",
        json={
            "phone_number": "+15551234567",
            "trigger_type": "payment_deadline_reminder",
            "days": 3,
        },
    )
    assert r.status_code == 200
    call_args = mock_send.call_args
    assert "3 days" in (call_args[0][1] if call_args[0] else "")


# --- Auth: when TRIGGER_API_KEY is set ---


def test_trigger_401_when_key_set_and_no_header():
    with patch.dict("os.environ", {"TRIGGER_API_KEY": "secret-key-123"}, clear=False):
        client_with_auth = TestClient(app)
        r = client_with_auth.post(
            "/api/trigger",
            json={"phone_number": "+15551234567", "trigger_type": "registration_opens"},
        )
    assert r.status_code == 401
    assert "detail" in r.json()
    assert "API key" in r.json()["detail"].lower() or "invalid" in r.json()["detail"].lower()


def test_trigger_401_when_key_set_and_wrong_token():
    with patch.dict("os.environ", {"TRIGGER_API_KEY": "secret-key-123"}, clear=False):
        client_with_auth = TestClient(app)
        r = client_with_auth.post(
            "/api/trigger",
            json={"phone_number": "+15551234567", "trigger_type": "registration_opens"},
            headers={"Authorization": "Bearer wrong-token"},
        )
    assert r.status_code == 401


@patch("trigger.sms_client.send_sms")
def test_trigger_200_when_key_set_and_correct_bearer(mock_send):
    mock_send.return_value = {"success": True, "message_id": "msg-auth-1", "error": None}
    with patch.dict("os.environ", {"TRIGGER_API_KEY": "secret-key-123"}, clear=False):
        client_with_auth = TestClient(app)
        r = client_with_auth.post(
            "/api/trigger",
            json={"phone_number": "+15551234567", "trigger_type": "registration_opens"},
            headers={"Authorization": "Bearer secret-key-123"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["message_id"] == "msg-auth-1"
    mock_send.assert_called_once()
