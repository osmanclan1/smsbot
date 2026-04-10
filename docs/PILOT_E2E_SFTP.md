# Pilot v1 — E2E testing with SFTP and fake phone numbers

Use this to exercise the **same shape** as production (secure file → cloud → SMS) without student PII.

## Principles

1. **Never** commit real student rosters. CSV fixtures must use **synthetic** E.164 numbers you are allowed to message (e.g. your own test handsets, or carrier-approved test numbers per Telnyx documentation).
2. **SFTP**: Production may use **AWS Transfer for SFTP** writing into the **same S3 bucket** prefix as manual uploads. For learning, any path that ends with a new object under `incoming/` on the pilot bucket is equivalent from the app’s perspective.

## AWS path (direct S3)

1. Deploy the stack: `./deploy/deploy-pilot.sh` from repo root.
2. Note outputs: **PilotInboundBucketName**, **WebhookUrl** (for Telnyx inbound tests).
3. Create a test CSV (example):

```csv
phone
+15551234567
```

Use numbers you **control** or that are explicitly for testing.

4. Upload:

```bash
aws s3 cp ./path/to/roster-fake.csv s3://YOUR_BUCKET/incoming/roster-fake.csv
```

5. Watch **CloudWatch** log groups for `smsbot-pilot-v1-ingest` and `smsbot-pilot-v1-sender`.
6. Confirm opt-out: text **STOP** to the pilot line, then rerun ingest; that number should be skipped.

## Local SFTP + S3 bridge (recommended for zero Transfer/EC2 cost)

Use this to practice **SFTP client → local folder → S3 `incoming/`** without AWS Transfer Family or a cloud SFTP endpoint.

### What it simulates

| Aspect | Local bridge |
|--------|----------------|
| SFTP client flow (Cyberduck, FileZilla, `sftp`) | Yes — connect to **localhost** (or your LAN IP). |
| S3 `ObjectCreated` → ingest Lambda | Yes — same trigger as `aws s3 cp` once the object exists under `incoming/`. |
| A district connecting over the public internet | **No** — they cannot SFTP to your laptop without VPN/tunnel. For that, use EC2 + SFTP, Transfer Family, or similar. |

### 1) Pick a local drop folder

Default used by the sync script: **`~/pilot-sftp-incoming`**. Override with env **`PILOT_SFTP_LOCAL_DIR`**.

Keep uploads **flat** at the root of that folder (e.g. `~/pilot-sftp-incoming/roster.csv`) so S3 keys are `incoming/roster.csv`, matching the Lambda’s `incoming/` prefix. Nested paths become `incoming/nested/...` and still work if they remain under `incoming/` in the bucket; avoid accidental `incoming/username/file.csv` unless you intend it.

### 2) Run a local SFTP server

**Option A — SFTPGo (macOS: `brew install sftpgo`)**

1. Start SFTPGo (follow Homebrew caveats for service vs foreground).
2. In the admin UI, create a user with **public-key** authentication only.
3. Set the user’s home directory to **`~/pilot-sftp-incoming`** (or your `PILOT_SFTP_LOCAL_DIR`).
4. Bind the SFTP listener to **127.0.0.1** unless remote testers on your LAN need access.

**Option B — OpenSSH (`sshd`)**

Use a dedicated Unix user and `ChrootDirectory` + `ForceCommand internal-sftp` so uploads land only in your chosen path. Platform-specific; follow current OpenSSH docs for your OS.

**Security:** Prefer key-based auth; do not expose port 22 to the world on untrusted networks.

### 3) Sync to S3

From the **repo root**, with AWS credentials working (`aws sts get-caller-identity`):

```bash
./scripts/pilot-local-sftp-bridge.sh
```

- Resolves **`PilotInboundBucketName`** from stack **`smsbot-pilot-v1-stack`** unless **`PILOT_INBOUND_BUCKET`** is set in `.env`.
- One-shot: uploads everything under the local folder to **`s3://BUCKET/incoming/`**.

Watch mode (after SFTP drops a file, waits ~2s, then syncs):

```bash
./scripts/pilot-local-sftp-bridge.sh --watch
```

Requires **`fswatch`** (macOS: `brew install fswatch`) or **`inotifywait`** (Linux: `inotify-tools`).

**`--delete`:** `aws s3 sync ... --delete` removes S3 objects under `incoming/` that are not present locally. Useful for a **personal** test bucket; **omit** on shared buckets or when you want history to accumulate in S3.

```bash
./scripts/pilot-local-sftp-bridge.sh --delete
```

### 4) IAM policy sketch (CLI principal running sync)

Least privilege for the sync user or your developer role (replace `BUCKET`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListIncomingPrefix",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::BUCKET",
      "Condition": {
        "StringLike": {
          "s3:prefix": ["incoming/", "incoming/*"]
        }
      }
    },
    {
      "Sid": "ReadWriteIncomingObjects",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::BUCKET/incoming/*"
    }
  ]
}
```

### 5) E2E checklist (local SFTP bridge)

1. Create a **synthetic** CSV (see [pilot-v1/ingest_handler.py](../pilot-v1/ingest_handler.py) for phone column names: `phone`, `phone_number`, `mobile`, `msisdn`, `cell`).
2. SFTP `put` the file into **`~/pilot-sftp-incoming/`** (or your `PILOT_SFTP_LOCAL_DIR`).
3. Run `./scripts/pilot-local-sftp-bridge.sh` (or use `--watch` beforehand).
4. Confirm the object in S3 under **`incoming/`**.
5. In CloudWatch, confirm **ingest** then **sender**; Telnyx should only hit numbers you control.

### 6) Optional billing guardrails

This bridge avoids **Transfer Family** and **EC2**, but **S3, Lambda, SQS, DynamoDB, and Telnyx** can still incur small charges per test.

- In **AWS Billing → Budgets**, create a monthly budget with email alerts for **actual and forecasted** spend (many teams use **$1–$5** thresholds for sandboxes).
- Review **Free Tier** / Cost Explorer so you know what your account is charged for.

## Managed / cloud SFTP (district-facing)

1. **AWS Transfer Family** (or another SFTP server) can map a user home to the pilot bucket **`incoming/`** prefix, **or**
2. Use the **local bridge** above for internal testing, or **EC2 + SFTPGo with S3 backend** if you need a public SFTP hostname without Transfer Family.

Upload the same **fake** CSV via SFTP, then verify **ingest** and **sender** as above.

## Campaign deadline smoke test

1. Deploy with a **near-term** `CampaignDeadlineIso` in the past (or set `CampaignActive=false`) via stack parameter update.
2. Upload a CSV; ingest should **not** enqueue sends (`error` in logs / early return).
3. Re-deploy with a **future** deadline to restore normal behavior.

## Local stack without AWS

- Run `uvicorn` in `pilot-v1` and use `POST /api/trigger` or `POST /api/campaign/send` with fake numbers; **DynamoDB-backed behavior** requires AWS or **DynamoDB Local** (not wired in this repo by default).
