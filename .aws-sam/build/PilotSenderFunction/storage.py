"""
Opt-out storage: DynamoDB when PILOT_DYNAMODB_TABLE is set, else in-memory (local dev).
"""
import os
from threading import Lock
from typing import Optional

from phone_utils import normalize_phone

try:
    import ddb
except ImportError:
    ddb = None  # type: ignore

_opt_outs: set[str] = set()
_lock = Lock()


def _ddb_enabled() -> bool:
    return bool(ddb and ddb.table_name())


def _opt_pk(phone: str) -> str:
    return f"OPT_OUT#{normalize_phone(phone)}"


def is_opted_out(phone_number: str) -> bool:
    """Return True if phone has opted out."""
    norm = normalize_phone(phone_number)
    if not norm:
        return False
    if _ddb_enabled():
        item = ddb.get_item(_opt_pk(norm), "META")
        return bool(item and item.get("opted_out", True))
    with _lock:
        return norm in _opt_outs


def opt_out(phone_number: str) -> None:
    """Mark phone as opted out."""
    norm = normalize_phone(phone_number)
    if not norm:
        return
    if _ddb_enabled():
        ddb.put_item(
            {
                "pk": _opt_pk(norm),
                "sk": "META",
                "opted_out": True,
            }
        )
        return
    with _lock:
        _opt_outs.add(norm)


def opt_in(phone_number: str) -> None:
    """Mark phone as opted in (remove from opt-out set)."""
    norm = normalize_phone(phone_number)
    if not norm:
        return
    if _ddb_enabled():
        ddb.delete_item(_opt_pk(norm), "META")
        return
    with _lock:
        _opt_outs.discard(norm)
