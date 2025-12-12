# SMS Bot for Oakton Community College

An intelligent SMS bot that helps students with registration, tuition payments, financial aid, and other college-related questions using AI-powered conversations.

## Features

- **Web Scraping**: Automatically collects information from Oakton Community College website
- **Knowledge Base**: Pinecone vector database for intelligent context retrieval
- **SMS Conversations**: Full two-way SMS conversations via Telnyx (no 10DLC required for demos)
- **Trigger System**: Initiate conversations via CSV upload or manual triggers
- **Admin Dashboard**: View conversations, transcripts, and results
- **AWS Deployment**: Infrastructure as code with SAM/CloudFormation
- **Conversation Intelligence**: GPT-4 powered responses with context from scraped website

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - PINECONE_API_KEY
# - TELNYX_API_KEY
# - TELNYX_PHONE_NUMBER
```

### 3. Populate Knowledge Base

```bash
python scripts/scrape_and_index.py
```

This scrapes the Oakton website and uploads content to Pinecone.

### 4. Local Development

**Backend:**
```bash
# Start FastAPI server
uvicorn src.api.main:app --reload --port 8000
```

**Frontend (Admin Dashboard):**
```bash
# Install Node dependencies (first time only)
npm install

# Development: Run Vite dev server (with hot reload)
npm run dev
# Then access: http://localhost:3000/admin

# OR: Build for production and serve via FastAPI
npm run build
# Then access: http://localhost:8000/admin
```

**API Documentation:**
```bash
open http://localhost:8000/docs
```

### 5. Deploy to AWS

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

```bash
sam build
sam deploy --guided
```

## Project Structure

```
smsbot/
├── src/
│   ├── scraper/          # Web scraping for Oakton pages
│   ├── api/              # FastAPI application
│   │   ├── routes/       # API endpoints
│   │   ├── services/     # Business logic
│   │   └── models/       # Data models
│   ├── storage/          # DynamoDB service layer
│   └── utils/            # Utility functions (finish() logger)
├── admin/                # Admin dashboard UI
├── scripts/              # Utility scripts
├── template.yaml         # AWS SAM CloudFormation template
└── requirements.txt      # Python dependencies
```

## Usage

### Trigger a Conversation

**Via Admin Dashboard:**
1. Click "Trigger Conversation" tab
2. Enter phone number (E.164 format: +1234567890)
3. Select trigger type
4. Click "Send Trigger"

**Via API:**
```bash
curl -X POST http://localhost:8000/api/admin/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "trigger_type": "overdue_balance"
  }'
```

**Via CSV Upload:**
1. Create CSV with format: `phone_number,metadata`
2. Upload via admin dashboard or API
3. System sends personalized messages to all numbers

### View Conversations

- **Admin Dashboard**: http://localhost:8000/admin
- **API**: `GET /api/admin/conversations`
- **API Detail**: `GET /api/admin/conversations/{conversation_id}`

### View Results

Results are logged when conversations complete via the `finish()` function.
- **Admin Dashboard**: Results tab
- **API**: `GET /api/admin/results`

## Trigger Types

### Account Issues
- `overdue_balance`: Student has outstanding balance
- `hold_on_account`: Hold preventing registration

### Payment Reminders (Phase 1)
- `payment_deadline_7days`: Payment deadline in 7 days
- `payment_deadline_3days`: Payment deadline in 3 days
- `payment_deadline_1day`: Payment deadline tomorrow

### Registration & Classes
- `not_registered`: Student hasn't registered for classes
- `registration_opens`: Registration period is opening
- `class_starts_soon`: Classes are starting soon
- `drop_deadline_warning`: Drop deadline approaching

### Financial Aid
- `financial_aid_deadline`: Financial aid deadline approaching

### Academic Support
- `advising_reminder`: Reminder to meet with advisor
- `graduation_checklist`: Help with graduation requirements

### General
- `upcoming_deadline`: Important deadline approaching (generic)

## Architecture

- **Backend**: FastAPI (Python 3.11+)
- **LLM**: OpenAI GPT-4
- **Vector DB**: Pinecone
- **SMS**: Telnyx (recommended - easier setup than Twilio)
- **Database**: DynamoDB (conversations, triggers, results)
- **Infrastructure**: AWS SAM/CloudFormation
- **Deployment**: AWS Lambda + API Gateway

## Configuration

All configuration is via environment variables. See `.env.example` for required variables.

## API Endpoints

- `POST /api/sms/webhook` - Telnyx webhook handler
- `POST /api/admin/trigger` - Manual trigger
- `POST /api/admin/trigger/csv` - CSV upload trigger
- `GET /api/admin/conversations` - List conversations
- `GET /api/admin/conversations/{id}` - Get conversation detail
- `GET /api/admin/results` - List results
- `GET /api/admin/triggers` - List triggers

## Development

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup and deployment instructions.

## License

MIT

