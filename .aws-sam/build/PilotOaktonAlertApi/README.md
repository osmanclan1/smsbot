# Oakton Alert Pilot

Single-purpose SMS bot for Oakton Summer pilot: tuition reminders and "Safe Removal" (withdraw to avoid fees). No general knowledge base; minimal or zero OpenAI (canned Q&A only).

## What it does

- **Keywords:** START (opt-in), STOP (opt-out), HELP (info) with fixed Oakton Alert copy.
- **Outbound:** Send one-time reminders via trigger types: `registration_opens`, `payment_deadline_final`, `payment_deadline_reminder`.
- **Inbound:** Replies are matched to intents and answered with canned responses: where to pay, withdraw, deadline, balance, refunds, registration/holds, financial aid, contact info, already paid, what is Oakton Alert, and MyOakton/login.

## Run locally

```bash
cd pilot-oakton-alert
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

- App: http://localhost:8001
- Webhook (Telnyx): `POST http://localhost:8001/api/sms/webhook` (use ngrok or similar for public URL)
- Trigger: `POST http://localhost:8001/api/trigger` with JSON: `{"phone_number": "+1...", "trigger_type": "registration_opens"}` or `payment_deadline_final` or `payment_deadline_reminder` (for reminder, add `"days": 3`). If `TRIGGER_API_KEY` is set, add header: `Authorization: Bearer $TRIGGER_API_KEY`. Example: `curl -X POST http://localhost:8001/api/trigger -H "Content-Type: application/json" -H "Authorization: Bearer $TRIGGER_API_KEY" -d '{"phone_number":"+15551234567","trigger_type":"registration_opens"}'`.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `TELNYX_API_KEY` | Telnyx API key |
| `TELNYX_PHONE_NUMBER` | Sender number (E.164) |
| `TELNYX_MESSAGING_PROFILE_ID` | Optional; required for toll-free |
| `TELNYX_PUBLIC_KEY` | Base64-encoded Ed25519 public key (Portal → Keys & Credentials) for webhook signature verification; if unset, verification is skipped (dev-friendly) |
| `TRIGGER_API_KEY` | Optional. If set, `POST /api/trigger` requires `Authorization: Bearer <this value>`. If unset, no auth is required (dev-friendly). |
| `OAKTON_ALERT_DEADLINE_TEXT` | Override deadline line for "when is deadline?" (default points to the public payment-options page) |
| `OAKTON_ALERT_MY_OAKTON_URL` | Student portal host or URL (default `my.oakton.edu`; normalized to `https://` in messages). Login required for balance and payment. |
| `OAKTON_ALERT_HELP_URL` | Default: oaktonalert.com |
| `OAKTON_ALERT_HELP_EMAIL` | Default: info@oaktonalert.com |
| `OAKTON_ALERT_PUBLIC_TUITION_FEES_URL` | Public tuition/fees/EZ Pay page (default `oakton.edu/.../tuition-and-fees.php`) |
| `OAKTON_ALERT_PUBLIC_PAYMENT_OPTIONS_URL` | Public payment schedules and EZ Pay (default `oakton.edu/.../payment-options.php`) |
| `OAKTON_ALERT_PUBLIC_FINANCIAL_AID_URL` | Public financial aid overview (default `oakton.edu/.../financial-aid/index.php`) |
| `OAKTON_ALERT_PUBLIC_WITHDRAWAL_URL` | Public withdrawal policy (default `oakton.edu/.../withdrawal-from-classes.php`) |
| `OAKTON_ALERT_PUBLIC_REGISTER_FOR_CLASSES_URL` | Public registration info (default `oakton.edu/.../register-for-classes.php`) |
| `OAKTON_ALERT_REGISTRATION_INFO` | Optional override for registration/holds intent (default uses public register URL + myOakton) |
| `OAKTON_ALERT_FINANCIAL_AID_INFO` | Optional override for financial aid intent (default uses public financial aid URL + myOakton) |
| `OAKTON_ALERT_CASHIER_CONTACT` | Optional override for contact/human intent (default includes Cashier and Enrollment Center phone numbers) |

## Testing

1. Expose local server (e.g. `ngrok http 8001`).
2. Set Telnyx SMS webhook to `https://your-ngrok-url/api/sms/webhook`.
3. Send START, STOP, HELP from your phone; then try "where do I pay?", "how do I withdraw?", "when is the deadline?".
4. Call trigger endpoint (curl or Postman) to send the two sample messages to a test number.

## Deploy to AWS (no server to keep running)

The pilot can run as a single Lambda behind API Gateway so you don't need to keep a local server or ngrok running.

**Prerequisites:** AWS CLI configured, [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) installed, Telnyx API key and phone number (and optionally `TELNYX_PUBLIC_KEY` for webhook verification and `TRIGGER_API_KEY` for trigger auth).

**Steps (from repo root):**

```bash
# Build the Lambda package
sam build -t deploy/template-pilot.yaml

# Deploy using Telnyx + optional keys from repo root .env (recommended)
./deploy/deploy-pilot.sh

# Or deploy (guided mode prompts for parameters)
sam deploy -t deploy/template-pilot.yaml --guided
# Or with config only: sam deploy -t deploy/template-pilot.yaml --config-file deploy/samconfig-pilot.toml
```

Ensure AWS credentials work (`aws sts get-caller-identity`). If you use `AWS_PROFILE` in `.env`, run `aws sso login --profile …` when you see `ExpiredToken`. The deploy script clears static `AWS_ACCESS_KEY_*` from `.env` when `AWS_PROFILE` is set so SSO is used.

**Deploy script notes:** `deploy/deploy-pilot.sh` uses **absolute** paths for `--config-file` and deploys **`.aws-sam/build/template.yaml`** after `sam build` (not `deploy/template-pilot.yaml`). Deploying the source template can upload **only app source** without `pip` deps, causing `Runtime.ImportModuleError: No module named 'fastapi'` on Lambda. Empty `TRIGGER_API_KEY` is omitted from `--parameter-overrides` because SAM rejects `TriggerApiKey=`.

**Lambda name:** This stack deploys the function as **`smsbot-pilot-oakton-alert-api`** so it does not collide with an older stack (`pilot-stack`) that may already own **`pilot-oakton-alert-api`** in the same account.

**Troubleshooting:** From repo root, with SSO (`source .env` then unset static AWS keys if using `AWS_PROFILE`): `./deploy/diagnose-pilot-stack.sh`

When prompted, provide at least `TelnyxApiKey` and `TelnyxPhoneNumber`. Optional: `TelnyxMessagingProfileId`, `TelnyxPublicKey`, `TriggerApiKey`, `OaktonAlertDeadlineText`, `OaktonAlertMyOaktonUrl`, and the `OaktonAlertPublic*` URLs (defaults match `config.py`).

**After deploy:**

1. Copy the **WebhookUrl** from the stack outputs (e.g. `https://xxx.execute-api.us-east-1.amazonaws.com/Prod/api/sms/webhook`).
2. In the Telnyx dashboard, set your messaging webhook URL to this **WebhookUrl**.
3. To send reminders, call the **TriggerUrl** (from outputs) with `POST` and JSON body; if you set `TRIGGER_API_KEY`, add header `Authorization: Bearer <key>`.

**Note:** Opt-out and rate limit are in-memory per Lambda instance. For production persistence across cold starts and instances, you can add a DynamoDB table and update `storage.py` later.

## Structure

- `messages.py` – All canned strings (START/STOP/HELP, trigger texts, fallback).
- `config.py` – URLs and deadline text (env overrides).
- `intents.py` – Intent patterns and canned replies (payment, withdrawal, deadline, balance, refunds, registration/holds, financial aid, contact, already paid, what is Oakton Alert, MyOakton/login).
- `storage.py` – Opt-out list (in-memory for local).
- `rate_limiter.py` – In-memory per-phone rate limit.
- `sms_client.py` – Telnyx send.
- `webhook.py` – Inbound SMS handler (keywords then intent match).
- `trigger.py` – Outbound reminder API.
- `main.py` – FastAPI app.
