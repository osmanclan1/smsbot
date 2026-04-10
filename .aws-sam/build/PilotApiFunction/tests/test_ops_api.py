"""Tests for pilot utility API endpoints: test send, campaign, and ops health."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@patch("ops_api.sms_client.send_sms")
def test_test_send_no_auth_with_trigger_type(mock_send):
    mock_send.return_value = {"success": True, "message_id": "msg-test-1", "error": None}
    r = client.post(
        "/api/test/send",
        json={"phone_number": "+15551234567", "trigger_type": "registration_opens"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["message_id"] == "msg-test-1"
    mock_send.assert_called_once()


@patch("ops_api.sms_client.send_sms")
def test_test_send_no_auth_with_custom_message(mock_send):
    mock_send.return_value = {"success": True, "message_id": "msg-test-2", "error": None}
    r = client.post(
        "/api/test/send",
        json={"phone_number": "5551234567", "message": "Hello from test endpoint"},
    )
    assert r.status_code == 200
    args, _ = mock_send.call_args
    assert args[0] == "5551234567"
    assert args[1] == "Hello from test endpoint"


def test_test_send_validation_rejects_both_trigger_and_message():
    r = client.post(
        "/api/test/send",
        json={
            "phone_number": "+15551234567",
            "trigger_type": "registration_opens",
            "message": "should fail",
        },
    )
    assert r.status_code == 422


def test_campaign_send_requires_auth_when_key_set():
    with patch.dict("os.environ", {"TRIGGER_API_KEY": "secret-key-123"}, clear=False):
        c = TestClient(app)
        r = c.post(
            "/api/campaign/send",
            json={
                "phone_numbers": ["+15551234567"],
                "trigger_type": "registration_opens",
            },
        )
    assert r.status_code == 401


@patch("ops_api.sms_client.send_sms")
def test_campaign_send_mixed_results(mock_send):
    import storage

    storage.opt_out("+15559990000")
    mock_send.side_effect = [
        {"success": True, "message_id": "m-ok", "error": None},
        {"success": False, "message_id": None, "error": "telnyx rejected"},
    ]
    try:
        with patch.dict("os.environ", {"TRIGGER_API_KEY": "secret-key-123"}, clear=False):
            c = TestClient(app)
            r = c.post(
                "/api/campaign/send",
                headers={"Authorization": "Bearer secret-key-123"},
                json={
                    "phone_numbers": [
                        "+15551230001",
                        "+15559990000",
                        "5551230002",
                        "not-a-number",
                    ],
                    "trigger_type": "registration_opens",
                },
            )
        assert r.status_code == 200
        data = r.json()
        assert data["totals"]["requested"] == 4
        assert data["totals"]["sent"] == 1
        assert data["totals"]["skipped"] == 1
        assert data["totals"]["failed"] == 2
        assert data["success"] is False
        assert len(data["results"]) == 4
        assert any(item["reason"] == "opted_out" for item in data["results"])
        assert any(item["reason"] == "invalid_phone_number" for item in data["results"])
        assert any(item["reason"] == "telnyx rejected" for item in data["results"])
    finally:
        storage.opt_in("+15559990000")


def test_campaign_send_validation_days_required_for_reminder():
    r = client.post(
        "/api/campaign/send",
        json={"phone_numbers": ["+15551234567"], "trigger_type": "payment_deadline_reminder"},
    )
    assert r.status_code == 422


def test_ops_health_masks_and_reports_flags():
    env = {
        "TELNYX_API_KEY": "abcd1234SECRET",
        "TELNYX_PHONE_NUMBER": "5551234567",
        "TELNYX_PUBLIC_KEY": "public-key-value",
        "TRIGGER_API_KEY": "campaign-secret",
    }
    with patch.dict("os.environ", env, clear=False):
        c = TestClient(app)
        r = c.get("/api/ops/health")
    assert r.status_code == 200
    data = r.json()
    checks = data["checks"]
    ready = data["ready"]
    assert checks["telnyx_api_key_present"] is True
    assert checks["telnyx_api_key_masked"] == "abcd...CRET"
    assert checks["telnyx_phone_normalized"] == "+15551234567"
    assert checks["trigger_api_auth_mode"] == "bearer"
    assert ready["outbound_sms"] is True
    assert ready["campaign_endpoint_protected"] is True
    assert ready["inbound_signature_verification_enabled"] is True
