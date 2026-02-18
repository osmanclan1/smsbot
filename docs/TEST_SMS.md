# Testing Your Toll-Free SMS Number

## Quick Test

### Option 1: Interactive Test (Recommended)
```bash
python test_sms.py
```

This will:
- Check your configuration
- Ask for recipient phone number
- Ask for message (or use default)
- Send the SMS
- Show results

### Option 2: Quick Command Line Test
```bash
python quick_test_sms.py +1234567890 "Hello! This is a test message from the SMS bot."
```

Replace:
- `+1234567890` with the recipient's phone number (E.164 format with +)
- `"Hello!..."` with your test message

## Update Your Phone Number

If you need to update the toll-free number in `.env`:

```bash
# Edit .env file
nano .env

# Or use this command (replace with your number):
echo 'TELNYX_PHONE_NUMBER=+1XXXXXXXXXX' >> .env
```

Make sure the number is in E.164 format: `+1` followed by 10 digits (e.g., `+18005551234`)

## Verify Configuration

Check your current setup:
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', '✅ Set' if os.getenv('TELNYX_API_KEY') else '❌ Missing'); print('Phone:', os.getenv('TELNYX_PHONE_NUMBER') or '❌ Missing')"
```

## Test Full Conversation Flow

To test the full bot conversation (receives message, processes, sends response):

1. **Set up webhook** (if testing locally, use ngrok or similar):
   ```bash
   # Install ngrok if needed
   brew install ngrok  # Mac
   
   # Start your FastAPI server
   uvicorn src.api.main:app --reload --port 8000
   
   # In another terminal, expose it
   ngrok http 8000
   ```

2. **Configure webhook in Telnyx dashboard**:
   - Go to Telnyx dashboard
   - Navigate to your phone number
   - Set webhook URL to: `https://your-ngrok-url.ngrok.io/api/sms/webhook`

3. **Send a test message** to your toll-free number from your phone

## Troubleshooting

### "Telnyx not configured" error
- Check `.env` file exists and has `TELNYX_API_KEY` and `TELNYX_PHONE_NUMBER`
- Make sure values don't have quotes around them in `.env`

### "401 Unauthorized" error
- Check your API key is correct
- Verify API key has SMS sending permissions in Telnyx dashboard

### "Phone number not verified" error
- Make sure your toll-free number is verified in Telnyx
- Check the number format is correct (E.164: +1XXXXXXXXXX)

### Message not received
- Check recipient number format (must be E.164: +1XXXXXXXXXX)
- Verify toll-free number can send to that destination
- Check Telnyx dashboard for delivery status


