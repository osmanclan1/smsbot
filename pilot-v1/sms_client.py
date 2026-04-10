"""
Minimal Telnyx SMS send for pilot. No dependency on main app.
"""
import os
from typing import Optional

import httpx

from phone_utils import normalize_phone

TELNYX_API_URL = "https://api.telnyx.com/v2/messages"


def send_sms(
    to_phone: str,
    message: str,
    messaging_profile_id: Optional[str] = None,
) -> dict:
    """
    Send SMS via Telnyx. Returns {"success": bool, "message_id": str|None, "error": str|None}.
    """
    api_key = os.getenv("TELNYX_API_KEY")
    from_phone = os.getenv("TELNYX_PHONE_NUMBER")
    if not api_key or not from_phone:
        print("⚠️  TELNYX_API_KEY or TELNYX_PHONE_NUMBER not set - mock send")
        return {"success": True, "message_id": "mock-id", "error": None}

    to_phone = normalize_phone(to_phone)
    from_phone = normalize_phone(from_phone)
    payload = {"to": to_phone, "from": from_phone, "text": message}
    if messaging_profile_id:
        payload["messaging_profile_id"] = messaging_profile_id
    elif os.getenv("TELNYX_MESSAGING_PROFILE_ID"):
        payload["messaging_profile_id"] = os.getenv("TELNYX_MESSAGING_PROFILE_ID")

    try:
        r = httpx.post(
            TELNYX_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        mid = data.get("data", {}).get("id")
        return {"success": True, "message_id": mid, "error": None}
    except Exception as e:
        err = str(e)
        # Only use .response for HTTP errors; timeouts/connection errors have no response
        response = getattr(e, "response", None)
        if response is not None:
            try:
                body = response.json()
                err = body.get("errors", [{}])[0].get("detail", err)
            except Exception:
                pass
        return {"success": False, "message_id": None, "error": err}
