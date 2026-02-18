"""
SMS webhook handler for Telnyx incoming messages.
"""

import time
from threading import Lock
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Optional
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from api.services.sms_service import SMSService
from api.services.conversation import ConversationEngine


router = APIRouter()

# Idempotency: avoid processing the same Telnyx message twice (retries/duplicate webhooks)
_PROCESSED_WEBHOOK_IDS: Dict[str, float] = {}
_PROCESSED_LOCK = Lock()
_WEBHOOK_ID_TTL_SECONDS = 86400  # 24 hours


def _check_and_mark_processed(message_id: Optional[str]) -> bool:
    """
    Return True if this message_id was already processed (duplicate), False otherwise.
    If not seen, mark as processed and return False.
    """
    if not message_id:
        return False
    now = time.time()
    with _PROCESSED_LOCK:
        # Prune expired entries
        expired = [k for k, v in _PROCESSED_WEBHOOK_IDS.items() if now - v > _WEBHOOK_ID_TTL_SECONDS]
        for k in expired:
            del _PROCESSED_WEBHOOK_IDS[k]
        if message_id in _PROCESSED_WEBHOOK_IDS:
            return True  # duplicate
        _PROCESSED_WEBHOOK_IDS[message_id] = now
        return False


def _strip_markdown_for_sms(text: str) -> str:
    """Remove Markdown bold (**) and asterisks so SMS reads cleanly."""
    if not text:
        return text
    return text.replace("**", "").strip()


def _send_webhook_to_queue(body: dict) -> bool:
    """Push webhook payload to SQS for async processing. Returns True on success."""
    queue_url = os.environ.get("WEBHOOK_QUEUE_URL")
    if not queue_url:
        print("⚠️  WEBHOOK_QUEUE_URL not set - cannot queue webhook")
        return False
    try:
        import boto3
        sqs = boto3.client("sqs")
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(body),
        )
        return True
    except Exception as e:
        print(f"⚠️  Failed to send webhook to SQS: {e}")
        return False


def process_incoming_webhook(body: dict) -> None:
    """
    Process a single message.received webhook (run in Processor Lambda).
    Idempotency, opt-out, conversation engine, send SMS. Raises on unexpected errors.
    """
    from storage.dynamodb import DynamoDBService
    from utils.rate_limiter import check_rate_limit, record_message

    event_data = body.get("data", {})
    payload = event_data.get("payload", {})
    message_id = payload.get("id")
    messaging_profile_id = payload.get("messaging_profile_id")

    # Idempotency
    try:
        db = DynamoDBService()
        should_skip = not db.try_claim_webhook_id(message_id)
    except Exception:
        should_skip = _check_and_mark_processed(message_id)
    if should_skip:
        print(f"⏭️  Duplicate webhook for message id {message_id} - skipping")
        return

    from_obj = payload.get("from") or {}
    from_number = from_obj.get("phone_number") if isinstance(from_obj, dict) else (from_obj if isinstance(from_obj, str) else "")
    from_number = (from_number or "").strip()
    message_text = (payload.get("text") or "").strip()

    if not from_number:
        print("⚠️  process_incoming_webhook: missing phone number")
        return

    if not from_number.startswith("+"):
        if from_number.startswith("1") and len(from_number) == 11:
            from_number = "+" + from_number
        elif len(from_number) == 10:
            from_number = "+1" + from_number

    message_upper = message_text.upper().strip() if message_text else ""
    OPT_OUT_KEYWORDS = ["STOP", "UNSUBSCRIBE", "CANCEL", "QUIT", "END", "OPT-OUT", "OPTOUT"]
    OPT_IN_KEYWORDS = ["START", "YES", "UNSTOP", "OPT-IN", "OPTIN", "SUBSCRIBE"]

    if message_upper in OPT_OUT_KEYWORDS:
        db = DynamoDBService()
        db.opt_out_student(from_number)
        sms_service = SMSService()
        sms_service.send_sms(from_number, "You've been unsubscribed from SMS messages. You won't receive any further texts. Reply 'START' to re-enable.", messaging_profile_id=messaging_profile_id)
        return
    if message_upper in OPT_IN_KEYWORDS:
        db = DynamoDBService()
        db.opt_in_student(from_number)
        sms_service = SMSService()
        sms_service.send_sms(from_number, "You've been subscribed to SMS messages. Reply 'STOP' anytime to unsubscribe.", messaging_profile_id=messaging_profile_id)
        return

    db = DynamoDBService()
    if db.is_student_opted_out(from_number):
        print(f"⚠️  Message from opted-out student {from_number} - ignoring")
        return
    if not message_text:
        print(f"Received empty message from {from_number}")
        return

    print(f"✅ Processing incoming SMS from {from_number}: {message_text[:50]}...")
    allowed, reason, retry_after = check_rate_limit(from_number)
    if not allowed:
        sms_service = SMSService()
        sms_service.send_sms(from_number, f"You've sent too many messages. Please wait {retry_after} seconds before sending another message.", messaging_profile_id=messaging_profile_id)
        return
    record_message(from_number)

    engine = ConversationEngine()
    result = engine.process_message(from_number, message_text)
    to_phone = from_number
    if to_phone and not to_phone.startswith("+"):
        if to_phone.startswith("1") and len(to_phone) == 11:
            to_phone = "+" + to_phone
        elif len(to_phone) == 10:
            to_phone = "+1" + to_phone

    if result.get("action") != "finish":
        response_text = _strip_markdown_for_sms(result.get("response", "") or "")
        if response_text:
            sms_service = SMSService()
            send_result = sms_service.send_sms(to_phone, response_text, messaging_profile_id=messaging_profile_id)
            if send_result.get("success"):
                print(f"✅ Response SMS sent to {to_phone} successfully")
            else:
                print(f"❌ Failed to send response SMS: {send_result.get('error')}")


def handle_webhook(event, context):
    """
    Ingestor: parse Telnyx webhook, push message.received to SQS, return 200 immediately.
    Processing runs in WebhookProcessor Lambda (SQS-triggered).
    """
    try:
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        event_data = body.get("data", {})
        event_type = event_data.get("event_type", "")
        if event_type != "message.received":
            return {"statusCode": 200, "body": json.dumps({"message": "Event type not handled"})}
        if not _send_webhook_to_queue(body):
            return {"statusCode": 500, "body": json.dumps({"error": "Failed to queue webhook"})}
        return {"statusCode": 200, "body": json.dumps({"success": True, "message": "Queued"})}
    except Exception as e:
        print(f"Error in webhook ingestor: {e}")
        import traceback
        traceback.print_exc()
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


@router.post("/webhook")
async def webhook_handler(request: Request):
    """
    Ingestor: parse Telnyx webhook, push message.received to SQS, return 200 immediately.
    If WEBHOOK_QUEUE_URL is not set (e.g. local dev), process inline instead.
    """
    try:
        body = await request.json()
        event_data = body.get("data", {})
        event_type = event_data.get("event_type", "")
        if event_type != "message.received":
            return {"message": "Event type not handled"}
        if _send_webhook_to_queue(body):
            return {"success": True, "message": "Queued"}
        # No queue (e.g. local): process inline so dev still works
        process_incoming_webhook(body)
        return {"success": True, "message": "Processed inline (no queue)"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in webhook ingestor: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

