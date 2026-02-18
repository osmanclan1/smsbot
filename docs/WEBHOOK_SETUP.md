# Telnyx Webhook Setup Guide

This guide explains how to configure the Telnyx webhook to receive incoming SMS messages.

## Webhook Endpoint

The webhook endpoint is: `/api/sms/webhook`

### Local Development

For local development, you'll need to expose your local server using a tool like ngrok:

1. **Install ngrok** (if not already installed):
   ```bash
   # Mac
   brew install ngrok
   
   # Or download from https://ngrok.com/download
   ```

2. **Start your FastAPI server**:
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```

3. **Expose it with ngrok** (in another terminal):
   ```bash
   ngrok http 8000
   ```

4. **Copy the HTTPS URL** from ngrok (e.g., `https://abc123.ngrok.io`)

5. **Configure in Telnyx Dashboard**:
   - Go to https://portal.telnyx.com/
   - Navigate to your phone number
   - Find "Messaging" or "Webhook" settings
   - Set webhook URL to: `https://your-ngrok-url.ngrok.io/api/sms/webhook`
   - Save settings

### Production Deployment

For production (AWS Lambda), the webhook URL will be:
```
https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/api/sms/webhook
```

Configure this URL in your Telnyx dashboard.

## Testing the Webhook

### Test with curl

```bash
# Simulate a webhook payload
curl -X POST http://localhost:8000/api/sms/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "event_type": "message.received",
      "payload": {
        "from": {"phone_number": "+1234567890"},
        "to": [{"phone_number": "+18334209112"}],
        "text": "Hello, this is a test message"
      }
    }
  }'
```

### Test with Real SMS

1. Send an SMS to your Telnyx phone number: `+18334209112`
2. The webhook should receive it and process it
3. You should receive an automated response

## Webhook Payload Format

Telnyx sends webhooks in this format:

```json
{
  "data": {
    "event_type": "message.received",
    "payload": {
      "from": {
        "phone_number": "+1234567890"
      },
      "to": [
        {
          "phone_number": "+18334209112"
        }
      ],
      "text": "Message content here"
    }
  }
}
```

## Troubleshooting

### Webhook Not Receiving Messages

1. **Check ngrok is running** (for local dev)
2. **Verify webhook URL in Telnyx dashboard** matches your endpoint
3. **Check server logs** for incoming requests
4. **Test webhook endpoint** with curl (see above)

### Messages Not Being Processed

1. **Check phone number format** - should be E.164 (+1234567890)
2. **Check server logs** for error messages
3. **Verify Telnyx API credentials** are set in `.env`
4. **Check conversation engine** is working (test with `/api/admin/test-chat`)

### Response Not Being Sent

1. **Check SMS service configuration** in `.env`:
   - `TELNYX_API_KEY`
   - `TELNYX_PHONE_NUMBER`
   - `TELNYX_MESSAGING_PROFILE_ID`

2. **Check server logs** for SMS send errors
3. **Verify phone number** can receive SMS from your Telnyx number

## Security Considerations

- Webhook endpoints should validate requests (optional: add signature verification)
- Use HTTPS in production
- Consider rate limiting for webhook endpoints
- Log all webhook activity for debugging

## Next Steps

After setting up the webhook:
1. Test with a real SMS message
2. Verify conversations are being saved
3. Check that responses are being sent
4. Monitor logs for any errors


