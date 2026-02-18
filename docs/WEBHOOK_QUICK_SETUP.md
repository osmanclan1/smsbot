# Quick Webhook Setup Guide

## The Problem

When you send SMS directly to the bot's phone number (`+18334209112`), it doesn't reply because:
- Telnyx needs to send a webhook to your server when it receives an SMS
- Your local server (`localhost:8000`) isn't accessible from the internet
- The webhook URL needs to be configured in Telnyx dashboard

## The Solution

Use **ngrok** to expose your local server to the internet, then configure the webhook URL in Telnyx.

## Quick Setup (Already Done!)

I've already started ngrok for you! Your webhook URL is:

```
https://stephan-backbreaking-corrinne.ngrok-free.dev/api/sms/webhook
```

## Next Steps

### 1. Configure Webhook in Telnyx Dashboard

1. Go to https://portal.telnyx.com/
2. Navigate to **Phone Numbers** → Find `+18334209112`
3. Click on the number to open settings
4. Look for **"Messaging"** or **"Webhook"** section
5. Set the webhook URL to:
   ```
   https://stephan-backbreaking-corrinne.ngrok-free.dev/api/sms/webhook
   ```
6. **Save** the settings

### 2. Test It

1. Send an SMS to `+18334209112` from your phone
2. Check your server logs - you should see:
   ```
   📥 INCOMING WEBHOOK RECEIVED
   ✅ Processing incoming SMS from +1...
   📤 Sending response SMS...
   ✅ Response SMS sent successfully!
   ```
3. You should receive a reply!

## If ngrok Stops

If you need to restart ngrok, run:
```bash
./setup_webhook.sh
```

Or manually:
```bash
ngrok http 8000
```

Then update the webhook URL in Telnyx dashboard with the new ngrok URL.

## Troubleshooting

### No Response After Configuring Webhook

1. **Check server logs** - Look for webhook requests
2. **Check ngrok dashboard** - http://localhost:4040 (see incoming requests)
3. **Verify webhook URL** in Telnyx matches exactly
4. **Test webhook manually**:
   ```bash
   curl -X POST http://localhost:8000/api/sms/webhook \
     -H "Content-Type: application/json" \
     -d '{"data": {"event_type": "message.received", "payload": {"from": {"phone_number": "+16699003917"}, "to": [{"phone_number": "+18334209112"}], "text": "Test"}}}'
   ```

### Webhook URL Changes

If ngrok restarts, you'll get a new URL. Update it in Telnyx dashboard.

### For Production

When you deploy to AWS Lambda/API Gateway, use your production URL instead of ngrok:
```
https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/api/sms/webhook
```


