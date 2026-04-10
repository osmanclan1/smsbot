"""
Oakton Alert pilot – SMS webhook (Telnyx message.received).
Keyword handling first, then intent-based canned responses. No OpenAI.
"""
import json
import os
import time
from threading import Lock
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

import messages
import phone_utils
import rate_limiter
import storage
import intents as intent_module
import sms_client
import webhook_verify

router = APIRouter()

OPT_OUT_KEYWORDS = {"stop", "unsubscribe", "cancel", "quit", "end", "opt-out", "optout"}
OPT_IN_KEYWORDS = {"start", "yes", "unstop", "opt-in", "optin", "subscribe"}
HELP_KEYWORDS = {"help", "info", "support", "?"}

_PROCESSED: dict[str, float] = {}
_PROCESSED_LOCK = Lock()
_ID_TTL = 86400  # 24h


def _is_duplicate(message_id: Optional[str]) -> bool:
    if not message_id:
        return False
    now = time.time()
    with _PROCESSED_LOCK:
        expired = [k for k, v in _PROCESSED.items() if now - v > _ID_TTL]
        for k in expired:
            del _PROCESSED[k]
        if message_id in _PROCESSED:
            return True
        _PROCESSED[message_id] = now
        return False


def _get_from_and_text(body: dict) -> tuple[str, str]:
    event_data = body.get("data", {})
    payload = event_data.get("payload", {})
    from_obj = payload.get("from") or {}
    from_number = from_obj.get("phone_number") if isinstance(from_obj, dict) else (from_obj if isinstance(from_obj, str) else "")
    from_number = (from_number or "").strip()
    text = (payload.get("text") or "").strip()
    return from_number, text


def _get_messaging_profile_id(body: dict) -> Optional[str]:
    event_data = body.get("data", {})
    payload = event_data.get("payload", {})
    return payload.get("messaging_profile_id")


def process_incoming(body: dict) -> None:
    """
    Process one Telnyx message.received webhook.
    Handles idempotency, opt-out check, keywords (START/STOP/HELP), then intent match.
    """
    event_data = body.get("data", {})
    payload = event_data.get("payload", {})
    message_id = payload.get("id")

    if _is_duplicate(message_id):
        return

    from_number, message_text = _get_from_and_text(body)
    if not from_number:
        return
    from_number = phone_utils.normalize_phone(from_number)
    if not from_number:
        return

    messaging_profile_id = _get_messaging_profile_id(body)

    # Normalize for keyword check
    msg_upper = message_text.upper().strip()
    msg_lower = message_text.lower().strip()

    # Opt-out
    if msg_lower in OPT_OUT_KEYWORDS:
        storage.opt_out(from_number)
        sms_client.send_sms(from_number, messages.OPT_OUT_RESPONSE, messaging_profile_id)
        return

    # Opt-in
    if msg_lower in OPT_IN_KEYWORDS:
        storage.opt_in(from_number)
        sms_client.send_sms(from_number, messages.OPT_IN_RESPONSE, messaging_profile_id)
        return

    # Help
    if msg_lower in HELP_KEYWORDS:
        sms_client.send_sms(from_number, messages.HELP_RESPONSE, messaging_profile_id)
        return

    # If opted out, ignore or send one-time reply
    if storage.is_opted_out(from_number):
        sms_client.send_sms(from_number, messages.OPTED_OUT_REPLY, messaging_profile_id)
        return

    if not message_text:
        return

    # Rate limit
    allowed, reason, retry_after = rate_limiter.check_rate_limit(from_number)
    if not allowed:
        sms_client.send_sms(
            from_number,
            f"Oakton Alert: You've sent too many messages. Please wait {retry_after} seconds.",
            messaging_profile_id,
        )
        return
    rate_limiter.record_message(from_number)

    # Intent match -> canned response
    response = intent_module.get_response_for_message(message_text)
    sms_client.send_sms(from_number, response, messaging_profile_id)


@router.post("/webhook")
async def webhook(request: Request):
    """Telnyx posts here. Expects JSON body with data.payload (from, text, id)."""
    raw_body = await request.body()
    public_key = os.getenv("TELNYX_PUBLIC_KEY", "").strip()

    if public_key:
        signature_header = request.headers.get("telnyx-signature-ed25519")
        timestamp_header = request.headers.get("telnyx-timestamp")
        if not webhook_verify.verify_telnyx_signature(
            raw_body, signature_header, timestamp_header, public_key
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid or missing webhook signature"},
            )
    else:
        print("Telnyx webhook signature verification skipped (TELNYX_PUBLIC_KEY not set)")

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid JSON body"},
        )
    try:
        process_incoming(body)
    except Exception as e:
        print(f"Webhook error: {e}")
        raise
    return {}
