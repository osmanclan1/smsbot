# Voice Agent Setup Guide

This guide walks you through setting up Telnyx Voice AI Agent integration with SMSBot.

## Prerequisites

1. Telnyx account with API access
2. Telnyx Voice AI Agent created in Mission Control Portal
3. Phone number assigned to Voice AI Agent
4. Backend server running and accessible via webhook URL

## Step 1: Create Telnyx Voice AI Agent

1. Log in to [Telnyx Mission Control Portal](https://portal.telnyx.com/)
2. Navigate to **AI, Storage and Compute** → **AI Assistants**
3. Click **Create New Assistant**
4. Choose **Blank Template** (we'll configure it ourselves)

## Step 2: Configure AI Assistant Agent

### Basic Configuration

- **Name**: `SMSBot Voice Assistant` (or your preferred name)
- **Model**: Choose a model that works well for real-time voice:
  - Recommended: `Qwen / Qwen3-235B-A22B` (no API key required)
  - Alternative: `OpenAI GPT-4` (requires OpenAI API key)
- **Instructions**: Use the following system prompt:

```
You're a proactive voice assistant for Oakton Community College. Help students with: tuition/payments (EZ Pay), registration, financial aid, deadlines, account holds, general info.

IMPORTANT - ACCURATE TUITION INFORMATION (use these exact amounts):
- In-District Students: $136.25 per credit hour (plus fees)
- Out-of-District Students (Illinois residents): $367.00 per credit hour (plus fees)
- Out-of-State Residents/International Students: $439.00 per credit hour (plus fees)

Always mention that fees are in addition to tuition per credit hour. If asked about total cost, explain it's tuition × credit hours + fees.

BE PROACTIVE: Offer next steps, break down tasks (1, 2, 3...), reference previous context, anticipate needs, use encouraging language.

STYLE: Friendly, conversational, natural speech. Speak clearly and at a comfortable pace. You can provide longer explanations than SMS. For URLs, spell them out clearly (e.g., "w w w dot oakton dot edu slash paying dash for dash college"). Number steps when helpful.

Call finish() when: action completed (paid/registered), issue resolved, student done, or conversation ends.

Result types: paid, registered, resolved, reminder_sent, escalated, no_response, abandoned.

Use provided context. Always be proactive and helpful.
```

- **Greeting**: 
  ```
  Hi! I'm your Oakton Community College assistant. I'm here to help with payments, registration, financial aid, and any questions you have. How can I assist you today?
  ```

### Advanced Options - Webhook Configuration

1. In the **Advanced Options** section, add a **Webhook** tool
2. Set the webhook URL to your backend endpoint:
   ```
   https://your-domain.com/api/voice/webhook
   ```
   Or for local testing with ngrok:
   ```
   https://your-ngrok-url.ngrok.io/api/voice/webhook
   ```
3. Configure webhook to send:
   - `transcript` - The transcribed user speech
   - `caller_id` or `phone_number` - The caller's phone number
   - `call_id` - The call identifier
   - `conversation_id` - The Telnyx conversation ID

## Step 3: Configure Voice Settings

1. **Language**: English (or your preferred language)
2. **Gender**: Choose based on your preference
3. **Provider**: Telnyx (recommended for best quality)
4. **Model**: NaturalHD
5. **Voice**: Test different voices and select one that fits your brand
6. **Transcription Model**: Choose a multilingual model if you expect non-English speakers

## Step 4: Enable Calling

1. When prompted, select **Yes** to enable inbound and outbound calls
2. For messaging, select **Not Now** (we handle SMS separately)

## Step 5: Assign Phone Number

1. In Mission Control Portal, go to **Real-Time Communications** → **Numbers**
2. If you don't have a number, click **Buy Numbers**
3. Search for and purchase a phone number
4. Go back to **AI Assistants** → Your assistant → **Calling** tab
5. Click **Assign Numbers**
6. Select your phone number and assign it to your assistant

## Step 4: Configure Environment Variables

Add to your `.env` file:

```bash
# Telnyx Voice AI Agent Configuration
TELNYX_VOICE_AGENT_ID=your-voice-agent-id
TELNYX_API_KEY=your-telnyx-api-key
TELNYX_PHONE_NUMBER=+1234567890  # Your Telnyx phone number
```

To find your Voice AI Agent ID:
1. Go to AI Assistants in Mission Control Portal
2. Click on your assistant
3. The ID is in the URL or in the assistant details

## Step 5: Test Webhook Connectivity

1. Start your backend server:
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```

2. Expose your server (if testing locally):
   ```bash
   ngrok http 8000
   ```

3. Update webhook URL in Telnyx Voice AI Agent with your ngrok URL

4. Test the webhook:
   ```bash
   curl -X POST https://your-ngrok-url.ngrok.io/api/voice/webhook \
     -H "Content-Type: application/json" \
     -d '{
       "transcript": "Hello, I need help with registration",
       "caller_id": "+1234567890",
       "call_id": "test-call-123"
     }'
   ```

5. You should receive a JSON response with a `response` field containing the assistant's reply

## Step 6: Test Voice Call

1. In Telnyx Mission Control Portal, go to your AI Assistant
2. Click **Test your assistant**
3. Click **Call assistant**
4. Your phone will ring - answer and have a conversation
5. The assistant should:
   - Answer with your configured greeting
   - Transcribe your speech
   - Call your webhook for processing
   - Speak the response from your backend

## Troubleshooting

### Webhook Not Receiving Requests

- Check that your webhook URL is publicly accessible
- Verify ngrok is running (if testing locally)
- Check Telnyx webhook logs in Mission Control Portal
- Ensure your backend server is running and the `/api/voice/webhook` endpoint exists

### Webhook Returns Errors

- Check backend logs for error messages
- Verify phone number normalization is working
- Ensure ConversationEngine is properly initialized
- Check that DynamoDB is accessible (if using)

### Voice Agent Not Responding

- Verify the webhook is returning valid JSON with a `response` field
- Check that the response text is not empty
- Ensure the Voice AI Agent model is properly configured
- Check Telnyx call logs for errors

### Conversation Not Shared Between SMS and Voice

- Verify that conversations are being created with the same phone number
- Check that `channel` field is being set correctly in conversations
- Ensure `get_conversation_by_phone()` is finding existing conversations

## Integration Flow

```
User calls Telnyx number
  ↓
Telnyx Voice AI Agent answers
  ↓
User speaks → Agent transcribes to text
  ↓
Agent calls webhook: POST /api/voice/webhook
  {
    "transcript": "user speech",
    "caller_id": "+1234567890",
    "call_id": "call-123"
  }
  ↓
Backend processes through ConversationEngine
  ↓
Returns JSON response:
  {
    "response": "Assistant reply text",
    "conversation_id": "conv-123"
  }
  ↓
Agent converts text to speech → User hears response
```

## Next Steps

- Test outbound voice calls via trigger system
- Monitor conversation quality and adjust prompts
- Set up call analytics and monitoring
- Configure call recordings (if needed)

## Support

For issues with:
- **Telnyx Voice AI Agent**: Check [Telnyx Documentation](https://developers.telnyx.com/)
- **Backend Integration**: Check server logs and webhook responses
- **Conversation Engine**: Review conversation.py and test with SMS first


