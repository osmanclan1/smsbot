# Deployment Guide

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. AWS SAM CLI installed (`brew install aws-sam-cli` or `pip install aws-sam-cli`)
3. Python 3.11+
4. API Keys:
   - OpenAI API key
   - Pinecone API key
   - Telnyx API key
5. Telnyx phone number (purchased/configured)

## Step 1: Populate Knowledge Base

Before deploying, scrape the Oakton website and populate Pinecone:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your_key"
export PINECONE_API_KEY="your_key"
export PINECONE_INDEX_NAME="oakton-knowledge-base"

# Run scraper
python scripts/scrape_and_index.py
```

This will:
- Scrape all Oakton website pages
- Process content into chunks
- Generate embeddings
- Upload to Pinecone

## Step 2: Configure Environment

Create `.env` file or set environment variables for deployment:

```bash
export OPENAI_API_KEY="your_openai_key"
export PINECONE_API_KEY="your_pinecone_key"
export PINECONE_INDEX_NAME="oakton-knowledge-base"
export TELNYX_API_KEY="your_telnyx_key"
export TELNYX_PHONE_NUMBER="+1234567890"
```

## Step 3: Deploy to AWS

```bash
# Build the application
sam build

# Deploy (guided mode - will prompt for parameters)
sam deploy --guided

# Or deploy with parameters file
sam deploy --parameter-overrides \
  OpenAIApiKey=$OPENAI_API_KEY \
  PineconeApiKey=$PINECONE_API_KEY \
  PineconeIndexName=$PINECONE_INDEX_NAME \
  TelnyxApiKey=$TELNYX_API_KEY \
  TelnyxPhoneNumber=$TELNYX_PHONE_NUMBER
```

After deployment, note the output URLs:
- `ApiUrl`: Your API endpoint
- `WebhookUrl`: Telnyx webhook URL

## Step 4: Configure Telnyx Webhook

1. Log into Telnyx dashboard
2. Navigate to Messaging → Webhooks
3. Create a new webhook pointing to the `WebhookUrl` from deployment
4. Select event type: `message.received`

## Step 5: Test

1. Access the admin dashboard (if served via API or separately)
2. Use the trigger button to send a test message
3. Reply to the message via SMS
4. Verify conversation is logged in admin dashboard

## Local Development

Run locally for testing:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your_key"
export PINECONE_API_KEY="your_key"
# ... etc

# Run FastAPI server
uvicorn src.api.main:app --reload --port 8000

# Access admin dashboard
open http://localhost:8000/admin

# API docs
open http://localhost:8000/docs
```

## Troubleshooting

### Lambda timeout
- Increase timeout in `template.yaml` Globals section

### Import errors
- Ensure all dependencies are in `requirements.txt`
- Check Lambda logs in CloudWatch

### DynamoDB errors
- Verify table names match environment variables
- Check IAM permissions in template

### Telnyx webhook not receiving
- Verify webhook URL is correct
- Check API Gateway logs
- Ensure webhook is configured in Telnyx dashboard

