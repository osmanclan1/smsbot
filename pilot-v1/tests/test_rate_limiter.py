"""Tests for in-memory rate limiter (issue 3)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rate_limiter


def test_under_limit_allowed():
    phone = "+15553333333"
    allowed, reason, retry = rate_limiter.check_rate_limit(phone)
    assert allowed is True
    assert reason is None
    assert retry is None


def test_after_recording_still_under_limit():
    phone = "+15554444444"
    for _ in range(3):
        rate_limiter.record_message(phone)
    allowed, _, _ = rate_limiter.check_rate_limit(phone)
    assert allowed is True


def test_over_limit_denied():
    # Use a unique number and hit the limit (10 per window)
    phone = "+15556666666"
    for _ in range(rate_limiter.MESSAGES_PER_WINDOW):
        rate_limiter.record_message(phone)
    allowed, reason, retry_after = rate_limiter.check_rate_limit(phone)
    assert allowed is False
    assert reason is not None
    assert "wait" in reason.lower() or "second" in reason.lower()
    assert retry_after is not None and retry_after >= 1


def test_returns_allowed_none_none_when_ok():
    phone = "+15557777777"
    allowed, reason, retry = rate_limiter.check_rate_limit(phone)
    assert allowed is True
    assert reason is None
    assert retry is None
