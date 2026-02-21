# Oakton Alert Pilot

Single-purpose SMS bot for Oakton Summer pilot: tuition reminders and "Safe Removal" (withdraw to avoid fees). No general knowledge base; minimal or zero OpenAI (canned Q&A only).

## What it does

- **Keywords:** START (opt-in), STOP (opt-out), HELP (info) with fixed Oakton Alert copy.
- **Outbound:** Send one-time reminders via trigger types: `registration_opens`, `payment_deadline_final`, `payment_deadline_reminder`.
- **Inbound:** Replies are matched to intents (where to pay, withdraw, deadline, balance, etc.) and answered with canned responses.

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
| `OAKTON_ALERT_DEADLINE_TEXT` | Default text for "when is deadline?" (e.g. "May 15") |
| `OAKTON_ALERT_MY_OAKTON_URL` | Default: my.oakton.edu |
| `OAKTON_ALERT_HELP_URL` | Default: oaktonalert.com |

## Testing

1. Expose local server (e.g. `ngrok http 8001`).
2. Set Telnyx SMS webhook to `https://your-ngrok-url/api/sms/webhook`.
3. Send START, STOP, HELP from your phone; then try "where do I pay?", "how do I withdraw?", "when is the deadline?".
4. Call trigger endpoint (curl or Postman) to send the two sample messages to a test number.

## Structure

- `messages.py` – All canned strings (START/STOP/HELP, trigger texts, fallback).
- `config.py` – URLs and deadline text (env overrides).
- `intents.py` – Intent patterns and canned replies for student questions.
- `storage.py` – Opt-out list (in-memory for local).
- `rate_limiter.py` – In-memory per-phone rate limit.
- `sms_client.py` – Telnyx send.
- `webhook.py` – Inbound SMS handler (keywords then intent match).
- `trigger.py` – Outbound reminder API.
- `main.py` – FastAPI app.
