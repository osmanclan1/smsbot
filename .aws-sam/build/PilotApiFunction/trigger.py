"""
Oakton Alert pilot – trigger API: send one-time reminder by trigger_type.
Respects opt-out; no conversation engine.
"""
import hmac
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

import messages
import storage
import sms_client

router = APIRouter()


async def verify_trigger_api_key(request: Request) -> None:
    """
    When TRIGGER_API_KEY is set, require Authorization: Bearer <key>.
    When unset, skip auth and log a warning (dev-friendly).
    """
    expected = os.getenv("TRIGGER_API_KEY", "").strip()
    if not expected:
        print("Trigger API authentication skipped (TRIGGER_API_KEY not set)")
        return
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    token = auth[7:].strip()
    if not token or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class TriggerRequest(BaseModel):
    phone_number: str = Field(..., description="E.164 or 10-digit US")
    trigger_type: str = Field(
        ...,
        description="registration_opens | payment_deadline_final | payment_deadline_reminder",
    )
    days: Optional[int] = Field(None, description="For payment_deadline_reminder: number of days until deadline")


def get_trigger_message(trigger_type: str, days: Optional[int] = None) -> str:
    return messages.format_trigger_message(trigger_type, days)


@router.post("/trigger")
async def trigger_reminder(req: TriggerRequest, _: None = Depends(verify_trigger_api_key)):
    """
    Send a one-time tuition reminder. Skips if number is opted out.
    When TRIGGER_API_KEY is set, requires Authorization: Bearer <key>.
    """
    if storage.is_opted_out(req.phone_number):
        return {
            "success": False,
            "skipped": True,
            "reason": "opted_out",
            "message_id": None,
        }

    try:
        text = get_trigger_message(req.trigger_type, req.days)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = sms_client.send_sms(req.phone_number, text)
    if result["success"]:
        return {
            "success": True,
            "skipped": False,
            "message_id": result.get("message_id"),
        }
    raise HTTPException(status_code=502, detail=result.get("error", "Failed to send SMS"))
