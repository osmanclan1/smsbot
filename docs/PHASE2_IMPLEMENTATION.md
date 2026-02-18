# Phase 2 Implementation Summary

Phase 2 improvements have been successfully implemented. This document outlines all the new features and how to use them.

## Features Implemented

### 1. Student Profile Storage

**What it does:**
- Stores student information (name, email, student ID, program, enrollment status)
- Automatically creates/updates profiles when triggers are sent with metadata
- Provides context to the AI during conversations

**How it works:**
- Trigger API accepts metadata with student info
- Profile is created/updated automatically when triggering conversations
- AI uses student profile context in responses (e.g., "Hi [Name], I see you're in the [Program] program...")

**Table:** `smsbot-students`
- **Primary Key:** `phone_number` (String)

**API Example:**
```json
{
  "phone_number": "+1234567890",
  "trigger_type": "payment_deadline_7days",
  "metadata": {
    "student_id": "S12345",
    "name": "John Doe",
    "email": "john@example.com",
    "program": "Computer Science",
    "enrollment_status": "full-time",
    "balance": 1500
  }
}
```

### 2. Calendar/Deadline Scraping

**What it does:**
- Scrapes Oakton's important dates page
- Extracts deadlines (payment, registration, drop dates, etc.)
- Categorizes deadlines automatically
- Stores in DynamoDB for easy querying

**How it works:**
- New `DeadlineScraper` class extracts dates and descriptions
- Automatically categorizes into: payment, registration, withdrawal, financial_aid, academic, graduation, holiday, general
- Parses various date formats (January 15, 2024, 01/15/2024, etc.)

**Table:** `smsbot-deadlines`
- **Primary Key:** `deadline_id` (String, UUID)
- **GSI:** `CategoryIndex` (category + date)

**Usage:**
```bash
# Sync deadlines from website
python scripts/sync_deadlines.py
```

**Deadline Structure:**
```json
{
  "deadline_id": "uuid",
  "date": "2024-01-15T00:00:00",
  "description": "Payment deadline for Spring 2024",
  "category": "payment",
  "date_text": "January 15, 2024",
  "url": "https://www.oakton.edu/academics/important-dates.php",
  "scraped_at": "2024-01-01T12:00:00",
  "days_until": 14
}
```

### 3. Follow-up Logic

**What it does:**
- Automatically schedules follow-up reminders
- Tracks when follow-ups are due
- Sends follow-up messages at the right time

**How it works:**
- When a trigger is sent (e.g., `payment_deadline_7days`), system schedules a follow-up
- Follow-up dates are calculated automatically:
  - `payment_deadline_7days` → follow up in 4 days (3 days before deadline)
  - `payment_deadline_3days` → follow up in 2 days (1 day before deadline)
  - Other deadline triggers → follow up 1 day before

**Table:** `smsbot-followups`
- **Primary Key:** `followup_id` (String, UUID)
- **GSI:** `PhoneNumberIndex` (phone_number + followup_date)
- **GSI:** `StatusDateIndex` (status + followup_date)

**Processing Follow-ups:**
```bash
# Process due follow-ups (run periodically, e.g., hourly)
python scripts/process_followups.py
```

**Follow-up Structure:**
```json
{
  "followup_id": "uuid",
  "phone_number": "+1234567890",
  "followup_date": "2024-01-12T12:00:00",
  "status": "pending",
  "trigger_type": "payment_deadline_7days_reminder",
  "conversation_id": "original_conversation_id",
  "metadata": {
    "original_trigger_id": "trigger_id"
  },
  "created_at": "2024-01-08T12:00:00"
}
```

### 4. Action Item Tracking

**What it does:**
- Tracks action items mentioned in conversations
- Extracts actionable steps from AI responses
- Allows tracking of task completion

**How it works:**
- AI responses are analyzed for action items (patterns like "Action:", "TODO:", numbered steps)
- Action items are automatically extracted and stored in conversation
- Can be marked as pending, in_progress, or completed

**Storage:**
- Action items are stored in the `conversations` table under the `action_items` field
- Each action item has: `action_id`, `action` (description), `status`, `created_at`, optional `due_date`

**Action Item Structure:**
```json
{
  "action_items": [
    {
      "action_id": "uuid",
      "action": "Pay online at myOakton",
      "status": "pending",
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```

## Database Schema

### New Tables

1. **smsbot-students**
   - Primary Key: `phone_number` (String)
   - Attributes: `student_id`, `name`, `email`, `program`, `enrollment_status`, `metadata`, `created_at`, `updated_at`

2. **smsbot-deadlines**
   - Primary Key: `deadline_id` (String)
   - GSI: `CategoryIndex` (category, date)
   - Attributes: `date`, `description`, `category`, `date_text`, `url`, `scraped_at`, `days_until`

3. **smsbot-followups**
   - Primary Key: `followup_id` (String)
   - GSI: `PhoneNumberIndex` (phone_number, followup_date)
   - GSI: `StatusDateIndex` (status, followup_date)
   - Attributes: `phone_number`, `followup_date`, `status`, `trigger_type`, `conversation_id`, `metadata`, `created_at`

### Updated Tables

- **smsbot-conversations**
  - Added: `action_items` (List) field

## Setup Instructions

### 1. Create Phase 2 Tables

**Option A: Using AWS CLI**
```bash
./scripts/create_phase2_tables.sh
```

**Option B: Using CloudFormation (SAM)**
```bash
sam build
sam deploy
```

### 2. Sync Deadlines (First Time)

```bash
python scripts/sync_deadlines.py
```

**Schedule this to run daily** (e.g., using cron or AWS EventBridge):
```bash
# Add to crontab for daily at 2 AM
0 2 * * * cd /path/to/smsbot && python scripts/sync_deadlines.py
```

### 3. Process Follow-ups (Regularly)

```bash
python scripts/process_followups.py
```

**Schedule this to run hourly** (e.g., using cron or AWS EventBridge):
```bash
# Add to crontab for every hour
0 * * * * cd /path/to/smsbot && python scripts/process_followups.py
```

### 4. Update Environment Variables (Optional)

Add to `.env`:
```bash
STUDENTS_TABLE=smsbot-students
DEADLINES_TABLE=smsbot-deadlines
FOLLOWUPS_TABLE=smsbot-followups
```

## Code Changes

### New Files
- `src/scraper/deadline_scraper.py` - Deadline scraping logic
- `scripts/sync_deadlines.py` - Script to sync deadlines from website
- `scripts/process_followups.py` - Script to process due follow-ups
- `scripts/create_phase2_tables.sh` - Script to create Phase 2 tables

### Updated Files
- `src/storage/dynamodb.py` - Added methods for students, deadlines, follow-ups, action items
- `src/api/services/conversation.py` - Added student profile/deadline context, action item extraction
- `src/api/routes/trigger.py` - Added student profile creation and follow-up scheduling
- `template.yaml` - Added Phase 2 table definitions

## Integration with AI

The AI now has access to:
1. **Student Profile Context:** Name, program, enrollment status, balance (if available)
2. **Upcoming Deadlines:** Top 5 most urgent deadlines (next 30 days)
3. **Action Items:** Automatically extracted from AI responses

This allows the AI to:
- Personalize responses ("Hi John, I see you're in Computer Science...")
- Reference upcoming deadlines ("Your payment deadline is in 14 days")
- Track action items mentioned in conversations

## Example Workflow

1. **Trigger with Student Info:**
   ```bash
   curl -X POST http://localhost:8000/api/admin/trigger \
     -H "Content-Type: application/json" \
     -d '{
       "phone_number": "+1234567890",
       "trigger_type": "payment_deadline_7days",
       "metadata": {
         "student_id": "S12345",
         "name": "John Doe",
         "balance": 1500
       }
     }'
   ```

2. **System:**
   - Creates/updates student profile
   - Creates trigger and conversation
   - Schedules follow-up for 4 days later
   - Sends initial message

3. **Follow-up (4 days later):**
   - `process_followups.py` runs
   - Finds due follow-up
   - Sends reminder message
   - Creates new conversation

4. **Conversation:**
   - AI has access to student profile and upcoming deadlines
   - Extracts action items from responses
   - Tracks completion

## Next Steps (Future Enhancements)

Potential Phase 3 improvements:
- Webhook integration for real-time follow-up processing
- Admin dashboard for viewing/managing action items
- Deadline notifications based on student's enrollment
- Analytics on follow-up effectiveness
- Action item completion tracking and reporting

