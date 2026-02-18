# Next Steps Implementation Guide

This document describes the additional production features implemented after the initial critical fixes.

## 1. Admin Notification Endpoints

### Overview
When conversations are escalated, admins are notified via webhook, API, or email (AWS SES or SMTP).

### Configuration

**Environment Variables:**
```bash
# Webhook notification
ADMIN_NOTIFICATION_WEBHOOK=https://your-admin-system.com/webhooks/escalations
ADMIN_WEBHOOK_AUTH_TOKEN=your-webhook-auth-token  # Optional

# Internal API notification
ADMIN_API_BASE_URL=https://your-admin-api.com
ADMIN_API_AUTH_TOKEN=your-api-auth-token  # Optional

# Email notification (AWS SES)
ADMIN_EMAIL=admin@oakton.edu
ADMIN_SENDER_EMAIL=noreply@oakton.edu
AWS_SES_REGION=us-east-1

# Email notification (SMTP fallback)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Usage

Escalations automatically trigger notifications when `finish()` is called with `result_type="escalated"`:

```python
finish(
    conversation_id="abc123",
    result_type="escalated",
    metadata={"reason": "Complex financial aid question requiring human review"}
)
```

**Notification Payload:**
```json
{
  "event_type": "conversation_escalated",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "conversation_id": "abc123",
    "phone_number": "+1234567890",
    "escalation_reason": "Complex financial aid question",
    "trigger_type": "financial_aid_deadline",
    "message_count": 8,
    "last_messages": [...],
    "metadata": {...}
  }
}
```

### Priority
1. Webhook (if `ADMIN_NOTIFICATION_WEBHOOK` is set)
2. API (if `ADMIN_API_BASE_URL` is set)
3. Email via SES (if `ADMIN_EMAIL` and AWS credentials are available)
4. Email via SMTP (if `SMTP_*` variables are set)

---

## 2. CloudWatch/Datadog Metrics Integration

### Overview
Structured metrics for observability - supports CloudWatch (AWS) and Datadog.

### Configuration

**Environment Variables:**
```bash
# Metrics provider: 'cloudwatch' or 'datadog' (default: 'cloudwatch')
METRICS_PROVIDER=cloudwatch

# CloudWatch (AWS)
AWS_REGION=us-east-1  # Uses default AWS credentials

# Datadog
METRICS_PROVIDER=datadog
DATADOG_API_KEY=your-datadog-api-key
DATADOG_APP_KEY=your-datadog-app-key  # Optional

# Metrics namespace (default: 'SMSBot')
METRICS_NAMESPACE=SMSBot
```

### Usage

**Increment Counter:**
```python
from utils.metrics import increment_counter

increment_counter('messages.received', tags={'channel': 'sms'})
increment_counter('conversations.started', tags={'trigger_type': 'payment_deadline_7days'})
```

**Set Gauge:**
```python
from utils.metrics import set_gauge

set_gauge('conversations.active', value=active_count)
set_gauge('conversations.in_flow.payment', value=payment_flow_count)
```

**Record Histogram (duration/timing):**
```python
from utils.metrics import record_histogram, metrics

# Manual timing
record_histogram('response_time_ms', response_time_ms, tags={'endpoint': '/webhook'})

# Context manager (automatic timing)
with metrics.timer('conversation.processing_time', tags={'flow': 'payment'}):
    # ... do work ...
    pass
```

### Recommended Metrics

**Counters:**
- `messages.received` - Incoming SMS messages
- `messages.sent` - Outgoing SMS messages
- `triggers.sent` - Triggers sent
- `triggers.suppressed` - Triggers suppressed (rate limiting/cooldown)
- `conversations.started` - New conversations
- `conversations.finished` - Completed conversations
- `conversations.escalated` - Escalated conversations
- `escalations.created` - Escalation events
- `opt_outs.recorded` - Opt-out requests

**Gauges:**
- `conversations.active` - Currently active conversations
- `conversations.in_flow.{flow_name}` - Conversations in specific flows
- `rate_limits.active` - Number of rate-limited phone numbers

**Histograms:**
- `response_time_ms` - API response times
- `conversation.processing_time` - Conversation processing duration
- `message.send_time_ms` - SMS send latency

---

## 3. Rate Limiting Per Phone Number

### Overview
Prevents SMS spam by limiting messages per phone number within a time window.

### Configuration

**Environment Variables:**
```bash
# Messages allowed per window (default: 10)
RATE_LIMIT_MESSAGES_PER_WINDOW=10

# Window size in seconds (default: 60)
RATE_LIMIT_WINDOW_SECONDS=60
```

### Default Limits
- **Messages per window:** 10 messages
- **Window size:** 60 seconds (1 minute)
- **Maximum limits:** 50 messages per hour (hard cap)

### Usage

Rate limiting is automatically enforced in SMS webhook handlers. When a rate limit is exceeded:

**Response:**
- Status: `429 Too Many Requests`
- Body: `{"success": false, "message": "...", "retry_after": 45}`
- User receives SMS: "You've sent too many messages. Please wait {retry_after} seconds..."

**Manual Check:**
```python
from utils.rate_limiter import check_rate_limit, record_message

allowed, reason, retry_after = check_rate_limit(phone_number)
if not allowed:
    # Handle rate limit
    print(f"Rate limited: {reason}, retry after {retry_after}s")
else:
    # Process message
    record_message(phone_number)  # Record after processing
```

### Rate Limit Behavior
- Sliding window: Messages expire after `RATE_LIMIT_WINDOW_SECONDS`
- Automatic cleanup: Old message timestamps are purged
- Per-phone tracking: Each phone number has independent limits

---

## 4. Conversation Timeout After Inactivity

### Overview
Automatically transitions conversations to `TIMEOUT` state after inactivity periods.

### Configuration

**Environment Variables:**
```bash
# Default timeout in hours (default: 72 = 3 days)
CONVERSATION_TIMEOUT_HOURS=72
```

### Timeout Periods by State

| State | Timeout Period |
|-------|---------------|
| `INIT` | 24 hours (if never responded) |
| `AWAITING_USER` | 72 hours (3 days) |
| `IN_FLOW` | 168 hours (7 days, more lenient) |
| Default | 72 hours (3 days) |

### Usage

**Manual Timeout Check (API Endpoint):**
```bash
# Check and timeout stale conversations
curl -X POST http://localhost:8000/admin/timeout-check
```

**Response:**
```json
{
  "status": "success",
  "timed_out_count": 3,
  "timed_out_conversations": ["conv-1", "conv-2", "conv-3"]
}
```

**Programmatic Check:**
```python
from utils.conversation_timeout import check_and_timeout_conversations, should_timeout_conversation

# Check all active conversations (batch)
timed_out_ids = check_and_timeout_conversations(limit=100)

# Check specific conversation
should_timeout, reason = should_timeout_conversation(conversation_id)
if should_timeout:
    print(f"Should timeout: {reason}")
```

### Scheduled Timeout Checks

**Option 1: AWS Lambda Scheduled Event (CloudWatch Events)**
```yaml
# In template.yaml
TimeoutChecker:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/
    Handler: utils.conversation_timeout.check_and_timeout_conversations
    Runtime: python3.11
    Events:
      Schedule:
        Type: Schedule
        Properties:
          Schedule: rate(1 hour)  # Run every hour
```

**Option 2: Cron Job (Local/EC2)**
```bash
# Add to crontab
0 * * * * curl -X POST http://localhost:8000/admin/timeout-check
```

**Option 3: CloudWatch EventBridge Rule**
```json
{
  "Rules": [{
    "Name": "smsbot-timeout-check",
    "ScheduleExpression": "rate(1 hour)",
    "Targets": [{
      "Arn": "arn:aws:lambda:...",
      "Id": "1"
    }]
  }]
}
```

### Timeout Behavior
- **State transition:** `AWAITING_USER` / `IN_FLOW` → `TIMEOUT`
- **Audit trail:** Transition recorded in `state_transitions` array
- **System message:** No automatic message to user (conversation silently times out)
- **Re-activation:** User can start new conversation by sending a message

---

## Integration Example

Here's how all features work together:

```python
# 1. Rate limiting (automatic in webhook)
from utils.rate_limiter import check_rate_limit, record_message

allowed, reason, retry_after = check_rate_limit(phone_number)
if not allowed:
    # Send rate limit message and return 429
    return {"status": 429, "retry_after": retry_after}

# 2. Process message
record_message(phone_number)
result = engine.process_message(phone_number, message_text)

# 3. Metrics (integrate in key locations)
from utils.metrics import increment_counter, record_histogram

increment_counter('messages.received', tags={'channel': 'sms'})
with metrics.timer('conversation.processing_time'):
    # Process conversation
    pass

# 4. Escalation (automatic notification)
if result_type == 'escalated':
    # Escalation service automatically sends notifications
    finish(conversation_id, 'escalated', metadata={'reason': '...'})
    increment_counter('conversations.escalated')

# 5. Timeout check (scheduled job)
from utils.conversation_timeout import check_and_timeout_conversations

# Run hourly via cron/Lambda scheduled event
timed_out = check_and_timeout_conversations(limit=100)
increment_counter('conversations.timed_out', value=len(timed_out))
```

---

## Deployment Checklist

1. **Admin Notifications:**
   - [ ] Set `ADMIN_NOTIFICATION_WEBHOOK` or `ADMIN_EMAIL`
   - [ ] Configure AWS SES or SMTP credentials
   - [ ] Test escalation notification

2. **Metrics:**
   - [ ] Set `METRICS_PROVIDER` (cloudwatch or datadog)
   - [ ] Configure AWS credentials (CloudWatch) or Datadog API keys
   - [ ] Verify metrics appear in dashboard

3. **Rate Limiting:**
   - [ ] Set `RATE_LIMIT_MESSAGES_PER_WINDOW` (default: 10)
   - [ ] Set `RATE_LIMIT_WINDOW_SECONDS` (default: 60)
   - [ ] Test rate limiting behavior

4. **Conversation Timeout:**
   - [ ] Set `CONVERSATION_TIMEOUT_HOURS` (default: 72)
   - [ ] Configure scheduled job (cron/Lambda/EventBridge)
   - [ ] Test timeout check endpoint

---

## Notes

- **Metrics:** Disabled if provider not configured (graceful degradation)
- **Rate Limiting:** Uses in-memory cache (fast) with DynamoDB fallback
- **Timeouts:** Terminal states (`RESOLVED`, `ESCALATED`, `TIMEOUT`) are never timed out
- **Notifications:** Multiple notification methods can be configured simultaneously (webhook + email)

All features are production-ready and can be enabled/disabled via environment variables.
