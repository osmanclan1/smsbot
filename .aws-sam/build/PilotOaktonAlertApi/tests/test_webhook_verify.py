"""Unit and integration tests for Telnyx webhook signature verification."""
import base64
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

import webhook_verify


def _make_keypair():
    """Return (private_key, public_key_bytes, public_key_base64)."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    public_key_b64 = base64.b64encode(public_key_bytes).decode("ascii")
    return private_key, public_key_bytes, public_key_b64


def _sign_payload(private_key, timestamp: str, raw_body: bytes) -> str:
    signed = timestamp.encode("utf-8") + b"|" + raw_body
    sig_bytes = private_key.sign(signed)
    return base64.b64encode(sig_bytes).decode("ascii")


# --- Unit tests for verify_telnyx_signature ---


def test_verify_valid_signature():
    raw_body = b'{"data":{"payload":{"id":"x"}}}'
    ts = str(int(time.time()))
    private_key, _, public_key_b64 = _make_keypair()
    signature = _sign_payload(private_key, ts, raw_body)
    assert webhook_verify.verify_telnyx_signature(
        raw_body, signature, ts, public_key_b64
    ) is True


def test_verify_invalid_signature():
    raw_body = b'{"data":{"payload":{"id":"x"}}}'
    ts = str(int(time.time()))
    _, _, public_key_b64 = _make_keypair()
    wrong_sig = base64.b64encode(b"x" * 64).decode("ascii")
    assert webhook_verify.verify_telnyx_signature(
        raw_body, wrong_sig, ts, public_key_b64
    ) is False


def test_verify_tampered_body_fails():
    raw_body = b'{"data":{"payload":{"id":"x"}}}'
    ts = str(int(time.time()))
    private_key, _, public_key_b64 = _make_keypair()
    signature = _sign_payload(private_key, ts, raw_body)
    tampered = b'{"data":{"payload":{"id":"y"}}}'
    assert webhook_verify.verify_telnyx_signature(
        tampered, signature, ts, public_key_b64
    ) is False


def test_verify_expired_timestamp_fails():
    raw_body = b'{"data":{}}'
    # Timestamp 10 minutes in the past
    ts = str(int(time.time()) - 600)
    private_key, _, public_key_b64 = _make_keypair()
    signature = _sign_payload(private_key, ts, raw_body)
    assert webhook_verify.verify_telnyx_signature(
        raw_body, signature, ts, public_key_b64
    ) is False


def test_verify_future_timestamp_beyond_tolerance_fails():
    raw_body = b'{"data":{}}'
    ts = str(int(time.time()) + 400)  # > 5 min in future
    private_key, _, public_key_b64 = _make_keypair()
    signature = _sign_payload(private_key, ts, raw_body)
    assert webhook_verify.verify_telnyx_signature(
        raw_body, signature, ts, public_key_b64
    ) is False


def test_verify_missing_signature_returns_false():
    raw_body = b'{"data":{}}'
    ts = str(int(time.time()))
    _, _, public_key_b64 = _make_keypair()
    assert webhook_verify.verify_telnyx_signature(
        raw_body, None, ts, public_key_b64
    ) is False
    assert webhook_verify.verify_telnyx_signature(
        raw_body, "", ts, public_key_b64
    ) is False


def test_verify_missing_timestamp_returns_false():
    raw_body = b'{"data":{}}'
    ts = str(int(time.time()))
    private_key, _, public_key_b64 = _make_keypair()
    signature = _sign_payload(private_key, ts, raw_body)
    assert webhook_verify.verify_telnyx_signature(
        raw_body, signature, None, public_key_b64
    ) is False
    assert webhook_verify.verify_telnyx_signature(
        raw_body, signature, "", public_key_b64
    ) is False


def test_verify_missing_public_key_returns_false():
    raw_body = b'{"data":{}}'
    ts = str(int(time.time()))
    private_key, _, public_key_b64 = _make_keypair()
    signature = _sign_payload(private_key, ts, raw_body)
    assert webhook_verify.verify_telnyx_signature(
        raw_body, signature, ts, None
    ) is False
    assert webhook_verify.verify_telnyx_signature(
        raw_body, signature, ts, ""
    ) is False


def test_verify_invalid_timestamp_format_returns_false():
    raw_body = b'{"data":{}}'
    _, _, public_key_b64 = _make_keypair()
    assert webhook_verify.verify_telnyx_signature(
        raw_body, "abc", "not-a-number", public_key_b64
    ) is False


# --- Integration: webhook route returns 403 when verification enabled and unsigned ---


def _webhook_body(from_number: str, text: str, message_id: str = "msg-sig-1"):
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
def test_webhook_unsigned_returns_403_when_public_key_set(mock_send):
    """When TELNYX_PUBLIC_KEY is set, request without valid signature gets 403."""
    from fastapi.testclient import TestClient
    from main import app

    private_key = Ed25519PrivateKey.generate()
    public_key_b64 = base64.b64encode(
        private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    ).decode("ascii")

    with patch.dict("os.environ", {"TELNYX_PUBLIC_KEY": public_key_b64}, clear=False):
        client = TestClient(app)
        body = _webhook_body("+15551234567", "help", "id-unsigned")
        r = client.post("/api/sms/webhook", json=body)
    assert r.status_code == 403
    assert "detail" in r.json()
    mock_send.assert_not_called()


@patch("webhook.sms_client.send_sms")
def test_webhook_signed_returns_200_when_public_key_set(mock_send):
    """When TELNYX_PUBLIC_KEY is set and request is signed, returns 200."""
    from fastapi.testclient import TestClient
    from main import app

    mock_send.return_value = {"success": True, "message_id": "m1", "error": None}
    body = _webhook_body("+15551234567", "help", "id-signed-1")
    raw_body = json.dumps(body).encode("utf-8")
    ts = str(int(time.time()))
    private_key = Ed25519PrivateKey.generate()
    public_key_b64 = base64.b64encode(
        private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    ).decode("ascii")
    signature = _sign_payload(private_key, ts, raw_body)

    with patch.dict("os.environ", {"TELNYX_PUBLIC_KEY": public_key_b64}, clear=False):
        client = TestClient(app)
        r = client.post(
            "/api/sms/webhook",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "telnyx-signature-ed25519": signature,
                "telnyx-timestamp": ts,
            },
        )
    assert r.status_code == 200
    assert r.json() == {}
    mock_send.assert_called_once()
