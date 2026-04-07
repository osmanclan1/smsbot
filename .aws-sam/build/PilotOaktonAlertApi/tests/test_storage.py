"""Tests for in-memory opt-out storage (issue 3)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import storage


def test_opt_out_then_is_opted_out():
    storage.opt_out("+15551111111")
    assert storage.is_opted_out("+15551111111") is True
    assert storage.is_opted_out("5551111111") is True
    assert storage.is_opted_out("(555) 111-1111") is True


def test_opt_in_removes_opt_out():
    storage.opt_out("+15552222222")
    assert storage.is_opted_out("+15552222222") is True
    storage.opt_in("+15552222222")
    assert storage.is_opted_out("+15552222222") is False
    storage.opt_in("5552222222")
    assert storage.is_opted_out("+15552222222") is False


def test_unknown_number_not_opted_out():
    assert storage.is_opted_out("+15559999999") is False
