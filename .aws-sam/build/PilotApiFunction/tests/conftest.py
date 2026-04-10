"""Ensure webhook tests skip Ed25519 verification when env has TELNYX_PUBLIC_KEY."""

import pytest


@pytest.fixture(autouse=True)
def clear_telnyx_public_key_for_http_tests(monkeypatch):
    monkeypatch.delenv("TELNYX_PUBLIC_KEY", raising=False)
