"""
SQS-triggered Lambda: process message.received webhooks (conversation + send SMS).
Telnyx already got 200 from the ingestor, so no retries. Idempotency still applied for at-least-once delivery.
"""

import json
import os
import sys

# Ensure project root is on path (Lambda runs with src as cwd)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes.sms import process_incoming_webhook


def handler(event, context):
    records = event.get("Records", [])
    for record in records:
        try:
            body_str = record.get("body", "{}")
            body = json.loads(body_str)
            event_data = body.get("data", {})
            if event_data.get("event_type") != "message.received":
                continue
            process_incoming_webhook(body)
        except json.JSONDecodeError as e:
            print(f"WebhookProcessor: invalid JSON in SQS message: {e}")
        except Exception as e:
            print(f"WebhookProcessor: error processing record: {e}")
            import traceback
            traceback.print_exc()
            raise  # Let Lambda retry this message
    return {"processed": len(records)}
