"""
Oakton Alert pilot - utility API endpoints for test sends, campaigns, and ops health.
"""
import os
import re
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

import phone_utils
import sms_client
import storage
from trigger import get_trigger_message, verify_trigger_api_key

router = APIRouter()


def _mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _is_valid_phone_number(phone_number: str) -> bool:
    normalized = phone_utils.normalize_phone(phone_number)
    return bool(re.fullmatch(r"\+\d{10,15}", normalized))


class TestSendRequest(BaseModel):
    phone_number: str = Field(..., description="Destination number (E.164 or US 10-digit)")
    trigger_type: Optional[str] = Field(
        None,
        description="registration_opens | payment_deadline_final | payment_deadline_reminder",
    )
    days: Optional[int] = Field(
        None, description="Required for payment_deadline_reminder when using trigger_type"
    )
    message: Optional[str] = Field(None, description="Direct custom message for one-off testing")

    @model_validator(mode="after")
    def validate_message_source(self):
        has_trigger = bool(self.trigger_type)
        has_message = bool((self.message or "").strip())
        if has_trigger == has_message:
            raise ValueError("Provide exactly one of trigger_type or message")
        if self.trigger_type == "payment_deadline_reminder" and self.days is None:
            raise ValueError("days is required for payment_deadline_reminder")
        return self


class CampaignSendRequest(BaseModel):
    phone_numbers: list[str] = Field(..., min_length=1, description="List of recipient numbers")
    trigger_type: str = Field(
        ...,
        description="registration_opens | payment_deadline_final | payment_deadline_reminder",
    )
    days: Optional[int] = Field(None, description="Required for payment_deadline_reminder")

    @model_validator(mode="after")
    def validate_campaign(self):
        if self.trigger_type == "payment_deadline_reminder" and self.days is None:
            raise ValueError("days is required for payment_deadline_reminder")
        return self


def _resolve_message(
    trigger_type: Optional[str], days: Optional[int], message: Optional[str]
) -> str:
    if message and message.strip():
        return message.strip()
    if not trigger_type:
        raise ValueError("trigger_type is required when message is not provided")
    return get_trigger_message(trigger_type, days)


@router.post("/test/send")
async def test_send(req: TestSendRequest):
    """
    One-off pilot send for demos/testing. Intentionally no auth.
    """
    try:
        text = _resolve_message(req.trigger_type, req.days, req.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = sms_client.send_sms(req.phone_number, text)
    if result["success"]:
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "phone_number": phone_utils.normalize_phone(req.phone_number),
        }
    raise HTTPException(status_code=502, detail=result.get("error", "Failed to send SMS"))


@router.post("/campaign/send")
async def campaign_send(
    req: CampaignSendRequest, _: None = Depends(verify_trigger_api_key)
):
    """
    Bulk pilot campaign send. Protected by TRIGGER_API_KEY when configured.
    """
    try:
        text = get_trigger_message(req.trigger_type, req.days)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sent = 0
    skipped = 0
    failed = 0
    results = []

    for raw_number in req.phone_numbers:
        number = phone_utils.normalize_phone(raw_number)
        if not _is_valid_phone_number(raw_number):
            failed += 1
            results.append(
                {
                    "phone_number": raw_number,
                    "success": False,
                    "skipped": False,
                    "reason": "invalid_phone_number",
                    "message_id": None,
                }
            )
            continue

        if storage.is_opted_out(number):
            skipped += 1
            results.append(
                {
                    "phone_number": number,
                    "success": False,
                    "skipped": True,
                    "reason": "opted_out",
                    "message_id": None,
                }
            )
            continue

        send_result = sms_client.send_sms(number, text)
        if send_result["success"]:
            sent += 1
            results.append(
                {
                    "phone_number": number,
                    "success": True,
                    "skipped": False,
                    "reason": None,
                    "message_id": send_result.get("message_id"),
                }
            )
        else:
            failed += 1
            results.append(
                {
                    "phone_number": number,
                    "success": False,
                    "skipped": False,
                    "reason": send_result.get("error", "send_failed"),
                    "message_id": None,
                }
            )

    return {
        "success": failed == 0,
        "trigger_type": req.trigger_type,
        "totals": {
            "requested": len(req.phone_numbers),
            "sent": sent,
            "skipped": skipped,
            "failed": failed,
        },
        "results": results,
    }


@router.get("/ops/health")
async def ops_health():
    """
    Operational readiness checks without sending SMS.
    """
    telnyx_api_key = os.getenv("TELNYX_API_KEY", "").strip()
    telnyx_phone = os.getenv("TELNYX_PHONE_NUMBER", "").strip()
    telnyx_public_key = os.getenv("TELNYX_PUBLIC_KEY", "").strip()
    trigger_api_key = os.getenv("TRIGGER_API_KEY", "").strip()

    normalized_sender = phone_utils.normalize_phone(telnyx_phone) if telnyx_phone else ""
    telnyx_ready = bool(
        telnyx_api_key and telnyx_phone and _is_valid_phone_number(telnyx_phone)
    )

    mode: Literal["open", "bearer"] = "bearer" if trigger_api_key else "open"

    return {
        "service": "Oakton Alert Pilot",
        "checks": {
            "telnyx_api_key_present": bool(telnyx_api_key),
            "telnyx_api_key_masked": _mask_secret(telnyx_api_key),
            "telnyx_phone_present": bool(telnyx_phone),
            "telnyx_phone_normalized": normalized_sender or None,
            "telnyx_public_key_present": bool(telnyx_public_key),
            "trigger_api_auth_mode": mode,
            "trigger_api_key_present": bool(trigger_api_key),
        },
        "ready": {
            "outbound_sms": telnyx_ready,
            "inbound_signature_verification_enabled": bool(telnyx_public_key),
            "campaign_endpoint_protected": bool(trigger_api_key),
        },
    }
