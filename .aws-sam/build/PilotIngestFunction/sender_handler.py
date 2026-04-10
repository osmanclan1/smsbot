"""
SQS-triggered Lambda: send one SMS per message; respects opt-out and idempotency.
"""
import json
import os
from typing import Any

import campaign_store

import messages
import sms_client
import storage


def handler(event: dict, context: Any) -> dict:
    sent = 0
    skipped = 0
    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
        except json.JSONDecodeError:
            print("Invalid JSON in SQS body")
            continue
        phone = body.get("phone")
        batch_id = body.get("batch_id")
        campaign_id = body.get("campaign_id", os.getenv("DEFAULT_CAMPAIGN_ID", "default"))
        trigger_type = body.get("trigger_type", "payment_deadline_reminder")
        days = body.get("days")
        if not phone or not batch_id:
            continue
        camp = campaign_store.get_campaign(campaign_id)
        if camp and not campaign_store.is_send_allowed(camp)[0]:
            skipped += 1
            continue
        if storage.is_opted_out(phone):
            skipped += 1
            continue
        if not campaign_store.try_mark_sent(batch_id, phone):
            skipped += 1
            continue
        try:
            text = messages.format_trigger_message(
                trigger_type,
                int(days) if days is not None else None,
            )
        except (ValueError, TypeError) as e:
            print(f"Bad trigger config: {e}")
            continue
        result = sms_client.send_sms(phone, text)
        if result.get("success"):
            sent += 1
        else:
            print(f"Send failed: {result.get('error')}")
    return {"sent": sent, "skipped": skipped}
