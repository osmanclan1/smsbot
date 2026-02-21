"""Tests for shared phone normalization."""
import sys
from pathlib import Path

# Ensure pilot-oakton-alert is on path when running tests from repo root or from pilot-oakton-alert
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from phone_utils import normalize_phone


def test_empty_returns_empty():
    assert normalize_phone("") == ""
    assert normalize_phone("   ") == ""


def test_10_digit_adds_plus_one():
    assert normalize_phone("5551234567") == "+15551234567"
    assert normalize_phone("555 123 4567") == "+15551234567"
    assert normalize_phone("555-123-4567") == "+15551234567"
    assert normalize_phone("(555) 123-4567") == "+15551234567"


def test_11_digit_leading_one():
    assert normalize_phone("15551234567") == "+15551234567"
    assert normalize_phone("1 555 123 4567") == "+15551234567"


def test_already_e164_unchanged():
    assert normalize_phone("+15551234567") == "+15551234567"


def test_strips_whitespace():
    assert normalize_phone("  +15551234567  ") == "+15551234567"
