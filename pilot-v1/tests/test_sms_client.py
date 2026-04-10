"""Tests for SMS client (exception handling when response is missing - issue 6)."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sms_client


@patch.dict("os.environ", {"TELNYX_API_KEY": "key", "TELNYX_PHONE_NUMBER": "+15551234567"}, clear=False)
@patch("sms_client.httpx.post")
def test_timeout_returns_failure_dict_no_crash(mock_post):
    """Exception without .response (e.g. timeout) must return {success: False, error: ...}."""
    mock_post.side_effect = TimeoutError("Connection timed out")
    result = sms_client.send_sms("+15559999999", "test")
    assert result["success"] is False
    assert result["message_id"] is None
    assert result["error"] is not None
    assert "timed out" in result["error"] or "Timeout" in result["error"]


@patch.dict("os.environ", {"TELNYX_API_KEY": "key", "TELNYX_PHONE_NUMBER": "+15551234567"}, clear=False)
@patch("sms_client.httpx.post")
def test_connection_error_returns_failure_dict(mock_post):
    """Connection error has no .response; must not assume e.response exists."""
    mock_post.side_effect = ConnectionError("Connection refused")
    result = sms_client.send_sms("+15559999999", "test")
    assert result["success"] is False
    assert result["error"] is not None
