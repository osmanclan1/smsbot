# Testing the SMS Bot

There are multiple ways to test the bot. Choose the one that works best for you!

## 🚀 Quick Start: Web Interface (Recommended)

The easiest way to test the bot is through the web interface.

### 1. Start the Server

```bash
./start_server.sh
```

Or manually:
```bash
uvicorn src.api.main:app --reload --port 8000
```

### 2. Open the Test Chat Interface

Navigate to: **http://localhost:8000/admin**

The **"Test Chat"** tab is now the default! Just type your questions and get instant responses.

### 3. Sample Questions to Try

Click the sample question buttons or type your own:

- **Payment Questions:**
  - "What are my payment options?"
  - "How do I pay my tuition?"
  - "What is EZ Pay?"
  - "When is the payment deadline?"

- **Tuition Questions:**
  - "How much does tuition cost?"
  - "What are the fees?"
  - "How much is in-district tuition?"

- **Registration Questions:**
  - "When does registration open?"
  - "How do I register for classes?"
  - "What classes are available?"

- **Financial Aid Questions:**
  - "How do I apply for financial aid?"
  - "What financial aid is available?"
  - "When is the FAFSA deadline?"

- **General Questions:**
  - "What are important dates?"
  - "How do I contact the enrollment center?"
  - "What happens if I don't pay on time?"

## 💻 Command Line Testing (Alternative)

If you have AWS credentials configured:

```bash
python scripts/test_bot_conversation.py
```

**Note:** This requires AWS credentials configured (for DynamoDB). If you get AWS errors, use the web interface instead.

## 📡 API Testing

You can also test via API directly:

### Test Chat Endpoint

```bash
curl -X POST http://localhost:8000/api/admin/test-chat \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+15555551234",
    "message": "What are my payment options?"
  }'
```

### Trigger a Conversation

```bash
curl -X POST http://localhost:8000/api/admin/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "trigger_type": "default"
  }'
```

### View API Documentation

Interactive API docs available at: **http://localhost:8000/docs**

## ✅ What to Test

1. **Knowledge Base Retrieval:** The bot should pull relevant context from scraped Oakton pages
2. **Response Quality:** Answers should be accurate and helpful
3. **Conversation Flow:** The bot should maintain context across multiple messages
4. **Multiple Topics:** Try different types of questions (payment, registration, financial aid)

## 🔍 Troubleshooting

### Server Won't Start

- Check if port 8000 is already in use
- Verify `.env` file has all required keys (OPENAI_API_KEY, PINECONE_API_KEY, etc.)
- Make sure dependencies are installed: `pip install -r requirements.txt`

### Bot Gives Generic Responses

- Check that knowledge base is populated: `python scripts/scrape_and_index.py`
- Verify Pinecone API key is correct
- Check OpenAI API key is valid

### AWS Errors

- If using command-line test script, ensure AWS credentials are configured
- For web interface, AWS is only needed when actually sending SMS (not for test chat)

## 📊 View Test Results

After testing, you can:

- **View Conversations:** http://localhost:8000/admin → "Conversations" tab
- **View Results:** http://localhost:8000/admin → "Results" tab

Enjoy testing! 🎉
