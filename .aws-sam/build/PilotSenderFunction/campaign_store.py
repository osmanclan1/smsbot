"""
Campaign and batch metadata in DynamoDB (same table as opt-outs).
Env fallbacks when table unavailable (local dev).
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from phone_utils import normalize_phone

try:
    import ddb
except ImportError:
    ddb = None  # type: ignore


def _pk_campaign(cid: str) -> str:
    return f"CAMPAIGN#{cid}"


def _pk_batch(bid: str) -> str:
    return f"BATCH#{bid}"


def _ttl_seconds(days: int) -> int:
    return max(0, days) * 24 * 60 * 60


def _ttl_days_from_env() -> int:
    raw = os.getenv("INGEST_MARKER_TTL_DAYS", "30")
    try:
        return max(1, int(raw))
    except ValueError:
        return 30


def _expires_at(days: int | None = None) -> int:
    ttl_days = _ttl_days_from_env() if days is None else max(1, days)
    return int(datetime.now(timezone.utc).timestamp()) + _ttl_seconds(ttl_days)


def get_campaign(campaign_id: str) -> Optional[dict[str, Any]]:
    """Return campaign META row or None."""
    if not ddb or not ddb.table_name():
        return _campaign_from_env(campaign_id)
    item = ddb.get_item(_pk_campaign(campaign_id), "META")
    if item:
        return item
    return _campaign_from_env(campaign_id)


def _campaign_from_env(campaign_id: str) -> Optional[dict[str, Any]]:
    default_id = os.getenv("DEFAULT_CAMPAIGN_ID", "default")
    if campaign_id != default_id:
        return None
    deadline = os.getenv("CAMPAIGN_DEADLINE_ISO", "").strip()
    active = os.getenv("CAMPAIGN_ACTIVE", "true").lower() in ("1", "true", "yes")
    trigger = os.getenv("DEFAULT_TRIGGER_TYPE", "payment_deadline_reminder")
    days_str = os.getenv("DEFAULT_REMINDER_DAYS", "3")
    try:
        days = int(days_str)
    except ValueError:
        days = 3
    if not deadline:
        # Local dev: far future so sends are allowed
        deadline = "2099-12-31T23:59:59Z"
    return {
        "pk": _pk_campaign(campaign_id),
        "sk": "META",
        "deadline_iso": deadline,
        "active": active,
        "default_trigger_type": trigger,
        "default_days": days,
    }


def ensure_campaign_seeded(campaign_id: str) -> None:
    """If DynamoDB is configured and campaign row missing, create from env."""
    if not ddb or not ddb.table_name():
        return
    if ddb.get_item(_pk_campaign(campaign_id), "META"):
        return
    base = _campaign_from_env(campaign_id)
    if base:
        ddb.put_item(base)


def is_send_allowed(campaign: dict[str, Any]) -> tuple[bool, str]:
    if not campaign.get("active", True):
        return False, "campaign_inactive"
    deadline_iso = campaign.get("deadline_iso") or ""
    if not deadline_iso:
        return True, "ok"
    try:
        # Accept Z suffix or offset-naive
        ds = deadline_iso.replace("Z", "+00:00")
        deadline = datetime.fromisoformat(ds)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if now > deadline:
            return False, "past_deadline"
    except (ValueError, TypeError):
        return True, "ok"
    return True, "ok"


def put_batch_meta(
    batch_id: str,
    campaign_id: str,
    s3_key: str,
    status: str,
    valid_rows: int,
    invalid_rows: int,
    queued: int,
    failed_enqueue: int = 0,
    dedup_skipped: int = 0,
) -> None:
    if not ddb or not ddb.table_name():
        print(
            f"[batch] {batch_id} status={status} valid={valid_rows} invalid={invalid_rows} "
            f"queued={queued} failed_enqueue={failed_enqueue} dedup_skipped={dedup_skipped}"
        )
        return
    ddb.put_item(
        {
            "pk": _pk_batch(batch_id),
            "sk": "META",
            "campaign_id": campaign_id,
            "s3_key": s3_key,
            "status": status,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "queued": queued,
            "failed_enqueue": failed_enqueue,
            "dedup_skipped": dedup_skipped,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": _expires_at(),
        }
    )


def new_batch_id() -> str:
    return str(uuid.uuid4())


def phone_sk_for_dedup(phone: str) -> str:
    return f"PHONE#{normalize_phone(phone)}"


def try_mark_sent(batch_id: str, phone: str) -> bool:
    """
    Idempotency: return True if this is the first send for (batch, phone).
    """
    if not ddb or not ddb.table_name():
        return True
    pk = _pk_batch(batch_id)
    sk = phone_sk_for_dedup(phone)
    return ddb.put_item_if_not_exists(
        {
            "pk": pk,
            "sk": sk,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": _expires_at(),
        }
    )


def _pk_ingest_marker(source_key: str, source_etag: str) -> str:
    return f"INGEST#{source_key}#{source_etag or 'noetag'}"


def try_mark_ingest_row(source_key: str, source_etag: str, row_index: int) -> bool:
    """
    Idempotency marker for ingest enqueue attempts.
    Returns True only the first time this row is seen for (key, etag, row_index).
    """
    if not ddb or not ddb.table_name():
        return True
    pk = _pk_ingest_marker(source_key, source_etag)
    sk = f"ROW#{row_index}"
    return ddb.put_item_if_not_exists(
        {
            "pk": pk,
            "sk": sk,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": _expires_at(),
        }
    )
