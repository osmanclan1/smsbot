# Pilot v1 hardening notes (2026-04-09)

Use this as a speaking guide for the CTO meeting.

## Current architecture status

- We moved from a script-style pilot to a durable, event-driven path:
  - S3 `incoming/` -> ingest Lambda -> SQS -> sender Lambda -> Telnyx.
- Inbound replies (STOP/START/HELP) are handled by API webhook and persisted in DynamoDB.
- Core state is stored in one DynamoDB table using PK/SK patterns for campaign, opt-out, batch, and dedup markers.

## What was improved in this sprint

1. **Double-fence compliance checks**
  - Campaign active/deadline check at ingest.
  - Campaign active/deadline check again at sender before SMS dispatch.
  - Value: protects against delayed queue messages crossing a policy boundary.
2. **Ingest reliability improvements**
  - Per-row `try/except` around enqueue call so one transient failure does not kill the full CSV job.
  - Row-level ingest idempotency markers prevent duplicate queueing when S3/Lambda retries happen.
  - Batch metadata now explicitly tracks `processing` -> `completed` / `completed_with_errors`.
3. **Sender dedup hardening**
  - Sender dedup marker write uses conditional put semantics to reduce race-driven duplicate sends.
4. **SQS operational hardening**
   - Added sender DLQ with redrive policy (max receives = 3).
   - Added CloudWatch alarm for DLQ visible messages > 0.
   - Added CloudWatch alarms on **ingest** Lambda **Errors** and **Throttles** (same optional SNS topic as DLQ).

5. **Least-privilege S3 read for ingest**
   - `PilotInboundBucketPolicy` grants `s3:GetObject` only on `incoming/*` to the ingest role (avoids IAM↔bucket circular dependency with S3-triggered Lambda).

6. **Timeout/visibility guardrail**
  - Sender timeout set to 45s.
  - Queue visibility timeout set to 180s.
  - Value: reduces duplicate processing caused by visibility expiring mid-run.

7. **DynamoDB TTL lifecycle**
  - Enabled DynamoDB TTL on `expires_at`.
  - Applied to transient rows (batch metadata and dedup markers).
  - Default TTL horizon controlled by `INGEST_MARKER_TTL_DAYS` (30 days default).

## Suggested meeting talking points (use verbatim)

- "We already enforce compliance gates at both ingest and send."
- "Next hardening sprint added DLQ, TTL lifecycle, and explicit timeout/visibility guardrails."
- "That gives us recoverability, lower ops noise, and controlled storage growth without redesigning core flow."

## What still remains (transparent next steps)

- Set stack parameter **`AlarmNotificationTopicArn`** (SNS topic) so ingest + DLQ alarms notify email/Slack/PagerDuty (optional; alarms still appear in CloudWatch without it).
- ~~Tighten ingest S3 access~~ **Done**: bucket policy limits **`GetObject`** to `incoming/*` for the ingest role only.
- Decide long-term retention policy for S3 source files and CloudWatch logs.
- Optional: move secrets from parameter-overrides/env to Secrets Manager reference flow.