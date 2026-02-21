"""
Oakton Alert pilot – opt-out storage.
In-memory for local testing; can be swapped for DynamoDB later (e.g. oakton-alert-opt-outs).
"""
from threading import Lock

from phone_utils import normalize_phone

_opt_outs: set[str] = set()
_lock = Lock()


def is_opted_out(phone_number: str) -> bool:
    """Return True if phone has opted out."""
    with _lock:
        return normalize_phone(phone_number) in _opt_outs


def opt_out(phone_number: str) -> None:
    """Mark phone as opted out."""
    with _lock:
        _opt_outs.add(normalize_phone(phone_number))


def opt_in(phone_number: str) -> None:
    """Mark phone as opted in (remove from opt-out set)."""
    with _lock:
        _opt_outs.discard(normalize_phone(phone_number))
