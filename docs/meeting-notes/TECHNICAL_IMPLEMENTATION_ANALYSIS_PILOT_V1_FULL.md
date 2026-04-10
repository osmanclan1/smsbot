# Technical Implementation Analysis (Full) — Pilot v1 (current)

Below is a detailed breakdown of what is implemented **as of the latest hardening pass**, how it works, and how it maps to the original plan. Use this for CTO / engineering review.

## 1) Scope Actually Delivered

Implementation is a **new active code line** in `pilot-v1/`, while `pilot-oakton-alert/` remains the **frozen baseline** in the repo.

**AWS deployment model**

- **Modern stack (pilot v1):** `smsbot-pilot-v1-stack` — deploy via `./deploy/deploy-pilot.sh` (see `deploy/samconfig-pilot.toml`).
- **Legacy stack (original single-Lambda pilot):** `smsbot-pilot-stack` — can be maintained separately so v1 does not overwrite legacy infra.

Delivered areas:

- App package: `pilot-v1/`
- Infra in `deploy/template-pilot.yaml`:
  - API Lambda (FastAPI + Mangum)
  - S3 inbound bucket (`incoming/` prefix triggers ingest)
  - Ingest Lambda (S3-triggered)
  - **Primary SQS queue** + **DLQ** + **CloudWatch alarm** on DLQ depth
  - Sender Lambda (SQS-triggered)
  - DynamoDB table with **TTL** on transient items
- Durable opt-out + **double-fence** campaign/deadline checks (ingest + sender)
- Sender + ingest **idempotency** (conditional Dynamo writes where applicable)
- Ingest **resilience** (per-row enqueue errors do not abort the whole CSV)
- Architecture docs, diagram export, SFTP E2E test guide, meeting notes
- Validation: `sam validate`, `sam build`, `pytest` in `pilot-v1/tests`

---

## 2) Repository / Structure Changes

### Top-level artifacts

- `pilot-v1/` — active pilot application
- `deploy/template-pilot.yaml` — SAM for v1 (S3 → ingest → SQS → sender + API + DynamoDB + DLQ)
- `deploy/samconfig-pilot.toml` — default stack `smsbot-pilot-v1-stack`
- `deploy/diagnose-pilot-stack.sh` — defaults to v1 stack name
- `docs/PILOT_ARCHITECTURE_V1.md`
- `docs/PILOT_E2E_SFTP.md`
- `docs/diagrams/pilot-architecture.mmd`, `.png`, `README.md`
- `docs/meeting-notes/` — CTO talking points + this document

### `pilot-v1` package additions / core modules

- `pilot-v1/ddb.py` — DynamoDB helpers, including `put_item_if_not_exists` for atomic idempotency markers
- `pilot-v1/campaign_store.py` — campaign metadata, deadline checks, batch metadata, ingest row markers, sender dedup markers, TTL via `expires_at`
- `pilot-v1/ingest_handler.py` — S3 CSV ingestion, SQS fan-out, batch lifecycle, per-row safety
- `pilot-v1/sender_handler.py` — SQS consumer → Telnyx send

### `pilot-v1` modifications

- `pilot-v1/storage.py` — DynamoDB-backed opt-out when `PILOT_DYNAMODB_TABLE` is set (in-memory fallback locally)
- `pilot-v1/messages.py` — `format_trigger_message(...)` shared by API and sender
- `pilot-v1/trigger.py` — uses `format_trigger_message`
- `pilot-v1/requirements.txt` — includes `boto3`
- `pilot-v1/tests/conftest.py` — clears `TELNYX_PUBLIC_KEY` for stable webhook tests

---

## 3) Infrastructure (SAM) — Technical Detail

File: `deploy/template-pilot.yaml`

### Resources

1. **DynamoDB — `PilotV1Table`**
  - Keys: `pk` (HASH), `sk` (RANGE)
  - Billing: `PAY_PER_REQUEST`
  - **TTL:** enabled on attribute `expires_at`
  - Note: only items that **include** `expires_at` are eligible for automatic expiry. **Opt-out** (`OPT_OUT#…`) and **campaign** (`CAMPAIGN#…`) rows written by current code **do not** set `expires_at`, so they are not TTL-deleted by default.
2. **S3 — `PilotInboundBucket`**
  - SSE-S3 (`AES256`)
  - Public access blocked
3. **S3 — `PilotInboundBucketPolicy`**
  - Allows **only** the ingest Lambda role to `s3:GetObject` on `incoming/*` in this bucket (avoids IAM inline policy referencing the bucket, which can create a circular dependency with S3-triggered Lambda).
4. **SQS — `PilotSendQueue`**
  - **VisibilityTimeout: 180s** (guardrail vs sender duration)
  - Retention: 14 days (`MessageRetentionPeriod: 1209600`)
  - **RedrivePolicy** → `PilotSendDLQ`, **maxReceiveCount: 3**
5. **SQS — `PilotSendDLQ`**
  - Failed messages (after max receives) land here for inspection
  - Stack output: `PilotSendDlqUrl`
6. **CloudWatch — `PilotSendDlqAlarm`**
  - Alarms when DLQ **ApproximateNumberOfMessagesVisible > 0**
  - Optional **AlarmActions**: stack parameter `**AlarmNotificationTopicArn`** (SNS)
7. **CloudWatch — ingest alarms**
  - `**PilotIngestErrorAlarm`**: Lambda **Errors** sum > 0 in 1 minute
  - `**PilotIngestThrottleAlarm`**: Lambda **Throttles** sum > 0 in 1 minute
  - Same optional SNS topic parameter for notifications
8. **Lambda — `PilotApiFunction`**
  - **No fixed `FunctionName`** in template (CloudFormation assigns physical name, e.g. `smsbot-pilot-v1-stack-PilotApiFunction-…`)
  - Handler: `main.handler`, Python 3.12, memory 256 MB (overrides global 512 for this function)
  - API Gateway: `/` and `/{proxy+}`
  - Env: Telnyx, campaign params, `PILOT_DYNAMODB_TABLE`, `SEND_QUEUE_URL`, `INGEST_MARKER_TTL_DAYS`
  - IAM: DynamoDB on table, SQS send to primary queue
9. **Lambda — `PilotIngestFunction`**
  - Handler: `ingest_handler.handler`, timeout **120s**, memory **512 MB**
  - Trigger: S3 `ObjectCreated` on `incoming/`
  - IAM: DynamoDB CRUD, SQS send; **S3 read** via `**PilotInboundBucketPolicy`** (not inline on the role)
10. **Lambda — `PilotSenderFunction`**
  - Handler: `sender_handler.handler`, timeout **45s**, memory 256 MB
    - Trigger: SQS event source mapping on primary queue, batch size 5
    - IAM: DynamoDB CRUD
    - **Timeout vs visibility:** 45s sender vs 180s visibility reduces duplicate in-flight delivery if Lambda runs long

### Parameters (policy + TTL)

- `CampaignDeadlineIso`, `CampaignActive`, `DefaultCampaignId`, `DefaultTriggerType`, `DefaultReminderDays`
- `IngestMarkerTtlDays` (default `30`) → env `INGEST_MARKER_TTL_DAYS` for `expires_at` on transient rows
- `AlarmNotificationTopicArn` (optional) → SNS notifications for **DLQ** + **ingest** alarms

### Outputs

- `ApiUrl`, `WebhookUrl`, `TriggerUrl`
- `PilotInboundBucketName`, `PilotV1TableName`, `PilotSendQueueUrl`
- `PilotSendDlqUrl`

---

## 4) Data Model in DynamoDB (Single-Table Pattern)

Implemented in `storage.py` and `campaign_store.py`:

### A) Opt-out records

- `pk = OPT_OUT#+1…`, `sk = META`, `opted_out: true`
- **No `expires_at`** in current writes → **not** subject to TTL cleanup

### B) Campaign metadata

- `pk = CAMPAIGN#{id}`, `sk = META` — deadline, active, defaults
- Seeded from env when missing (`ensure_campaign_seeded`)
- **No `expires_at`** on seeded campaign row in current code

### C) Batch metadata

- `pk = BATCH#{batch_id}`, `sk = META`
- Fields include: `status`, `valid_rows`, `invalid_rows`, `queued`, `failed_enqueue`, `dedup_skipped`, `updated_at`, `expires_at`
- Status flow: `processing` at start of file → `completed` or `completed_with_errors`

### D) Ingest row idempotency markers

- `pk = INGEST#{s3_key}#{eTag|noetag}`, `sk = ROW#{row_index}`
- `expires_at` set (transient)
- **Conditional put** (`attribute_not_exists(pk)`) via `ddb.put_item_if_not_exists`

### E) Sender dedup keys (per batch + phone)

- `pk = BATCH#{batch_id}`, `sk = PHONE#+1…`
- `**expires_at`** set (transient)
- `try_mark_sent` uses **conditional put** — first writer wins; duplicates get `ConditionalCheckFailed` → treated as already sent

---

## 5) Runtime Flow (End-to-End)

### Flow 1: Roster ingestion (S3 → SQS)

File: `pilot-v1/ingest_handler.py`

1. S3 event for object under `incoming/`.
2. Load campaign; **gate** on active + deadline.
3. `put_batch_meta(..., status="processing")` early.
4. **Still reads full object into memory** (`get_object` → `read()` → `decode`) — acceptable for ~100-row pilot; **OOM risk remains** for very large files.
5. Parse CSV; per row: validate phone, skip opt-outs, build payload.
6. **Ingest idempotency:** `try_mark_ingest_row(key, etag, row_index)` before enqueue (skips on retry if marker exists).
7. `sqs.send_message` in `try/except`: failures increment `failed_enqueue`, loop continues.
8. Final `put_batch_meta` with `completed` or `completed_with_errors` and full counters.

### Flow 2: Sender worker (SQS → Telnyx)

File: `pilot-v1/sender_handler.py`

1. Parse body; validate `phone` + `batch_id`.
2. Re-check campaign gate (second fence).
3. Re-check opt-out.
4. `try_mark_sent` (conditional dedup).
5. Build message via `format_trigger_message`, call Telnyx.
6. On repeated failures, SQS retries; after **3** receives, message moves to **DLQ** (no silent loss).

### Flow 3: Inbound + opt-out

- Telnyx → API Gateway → `webhook.py` → `storage.opt_out` / `opt_in`
- **Webhook duplicate-id map remains in-process** (not cross-instance durable) — known gap for inbound idempotency at scale.

---

## 6) Message / Trigger Logic

- `messages.format_trigger_message` shared by `trigger.py` and `sender_handler.py` to avoid template drift.

---

## 7) Local vs Cloud

- **Cloud:** DynamoDB + SQS + DLQ + TTL as above.
- **Local (no `PILOT_DYNAMODB_TABLE`):** in-memory opt-out; ingest row markers and sender dedup logic degrade to “always first attempt” style behavior where helpers no-op to True — use AWS or explicit local Dynamo for faithful behavior.

---

## 8) Security / Compliance / Ops

**In place**

- S3 encryption + blocked public access
- Durable opt-outs in DynamoDB
- Double-fence deadline/active checks
- DLQ + DLQ depth alarm resource
- TTL on transient dedup/ingest/batch-meta rows (cost + clutter control)
- Per-row ingest enqueue resilience

**Still recommended (not fully done in template)**

- Set `**AlarmNotificationTopicArn`** at deploy time (or subscribe in console) so **DLQ + ingest** alarms notify a human
- **Secrets Manager** (or SSM) for Telnyx secrets instead of only deploy parameters
- **S3 lifecycle** on `incoming/` objects; log retention policy
- Stronger **inbound webhook idempotency** (Dynamo vs in-memory)

---

## 9) Documentation

- `docs/PILOT_ARCHITECTURE_V1.md` — updated with hardening section
- `docs/PILOT_E2E_SFTP.md`
- `docs/diagrams/`*
- `docs/meeting-notes/pilot-v1-hardening-notes-2026-04-09.md` — talking points
- This file: `docs/meeting-notes/TECHNICAL_IMPLEMENTATION_ANALYSIS_PILOT_V1_FULL.md`

---

## 10) Validation

- `sam validate -t deploy/template-pilot.yaml` — valid
- `sam build` via `deploy/deploy-pilot.sh`
- `pytest` in `pilot-v1/tests` — **57 passed** (re-run after changes in CI/local)

---

## 11) Plan Mapping

- Separate v1 code line + v1 stack: **Done**
- S3 → ingest → SQS → sender → Telnyx: **Done**
- Durable opt-out + deadline gating: **Done**
- Docs + E2E guide: **Done**
- Reliability hardening (DLQ, TTL, visibility/timeout, ingest/sender idempotency improvements): **Done in code/template; deploy to confirm stack outputs**

---

## 12) Remaining Caveats / Risks

1. **Full-object read in ingest** — OOM if roster files grow unexpectedly; streaming parse is a future improvement.
2. **Inbound webhook dedup** — still primarily in-memory per Lambda instance.
3. **SQS + sender** — at-least-once delivery is mitigated by conditional dedup; edge cases around visibility vs timeout should stay monitored if timeouts or Telnyx latency change.

---

## Meeting one-liners (from hardening notes)

- “We already enforce compliance gates at both ingest and send.”
- “We added DLQ, TTL lifecycle, and explicit timeout/visibility guardrails.”
- “That gives recoverability, lower ops noise, and controlled storage growth without redesigning core flow.”