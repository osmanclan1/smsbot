"""
S3-triggered Lambda: parse roster CSV, validate phones, enqueue SMS jobs to SQS.
"""
import csv
import io
import json
import os
from typing import Any

import boto3

import campaign_store
import storage
from phone_utils import normalize_phone

PHONE_KEYS = ("phone", "phone_number", "mobile", "msisdn", "cell")


def _pick_phone(row: dict[str, Any]) -> str:
    lower = {k.lower().strip(): v for k, v in row.items() if k}
    for key in PHONE_KEYS:
        if key in lower and str(lower[key]).strip():
            return str(lower[key]).strip()
    if row:
        first = next(iter(row.values()))
        return str(first or "").strip()
    return ""


def _pick_optional(row: dict[str, Any], key: str) -> str:
    lower = {k.lower().strip(): v for k, v in row.items() if k}
    v = lower.get(key.lower())
    return str(v).strip() if v is not None else ""


def handler(event: dict, context: Any) -> dict:
    queue_url = os.getenv("SEND_QUEUE_URL", "").strip()
    if not queue_url:
        print("SEND_QUEUE_URL not set; nothing to enqueue")
        return {"ok": False, "error": "missing_SEND_QUEUE_URL"}

    campaign_id = os.getenv("DEFAULT_CAMPAIGN_ID", "default")
    campaign_store.ensure_campaign_seeded(campaign_id)
    campaign = campaign_store.get_campaign(campaign_id)
    if not campaign:
        print("No campaign config")
        return {"ok": False, "error": "no_campaign"}

    allowed, reason = campaign_store.is_send_allowed(campaign)
    if not allowed:
        print(f"Campaign not allowing sends: {reason}")
        return {"ok": False, "error": reason}

    sqs = boto3.client("sqs", region_name=os.getenv("AWS_REGION", "us-east-1"))
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))

    processed = 0
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        etag = str(record["s3"]["object"].get("eTag", "") or "")
        batch_id = campaign_store.new_batch_id()
        body_bytes = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        text = body_bytes.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        valid = 0
        invalid = 0
        queued = 0
        failed_enqueue = 0
        dedup_skipped = 0
        row_index = 0
        default_trigger = campaign.get("default_trigger_type", "payment_deadline_reminder")
        try:
            default_days = int(campaign.get("default_days", 3) or 3)
        except (TypeError, ValueError):
            default_days = 3

        campaign_store.put_batch_meta(
            batch_id,
            campaign_id,
            key,
            "processing",
            valid,
            invalid,
            queued,
            failed_enqueue=failed_enqueue,
            dedup_skipped=dedup_skipped,
        )

        for row in reader:
            processed += 1
            row_index += 1
            raw_phone = _pick_phone(row)
            if not raw_phone:
                invalid += 1
                continue
            phone = normalize_phone(raw_phone)
            if not phone:
                invalid += 1
                continue
            valid += 1
            if storage.is_opted_out(phone):
                continue
            trig = _pick_optional(row, "trigger_type") or default_trigger
            days_str = _pick_optional(row, "days")
            days: int | None = None
            if days_str:
                try:
                    days = int(days_str)
                except ValueError:
                    days = default_days
            else:
                days = default_days if trig == "payment_deadline_reminder" else None

            payload = {
                "batch_id": batch_id,
                "phone": phone,
                "campaign_id": campaign_id,
                "trigger_type": trig,
                "days": days,
            }
            if not campaign_store.try_mark_ingest_row(key, etag, row_index):
                dedup_skipped += 1
                continue
            try:
                sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(payload))
                queued += 1
            except Exception as e:
                failed_enqueue += 1
                print(f"Failed to enqueue row={row_index} key={key}: {e}")

        status = "completed_with_errors" if failed_enqueue > 0 else "completed"
        campaign_store.put_batch_meta(
            batch_id,
            campaign_id,
            key,
            status,
            valid,
            invalid,
            queued,
            failed_enqueue=failed_enqueue,
            dedup_skipped=dedup_skipped,
        )
        print(
            f"Ingest batch_id={batch_id} key={key} valid={valid} invalid={invalid} queued={queued} "
            f"failed_enqueue={failed_enqueue} dedup_skipped={dedup_skipped} status={status}"
        )

    return {"ok": True, "processed_records": processed}
