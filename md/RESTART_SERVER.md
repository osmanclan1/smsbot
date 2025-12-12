# Restart Server Instructions

## Quick Restart

Your server needs to be restarted to pick up the AWS profile configuration.

### Step 1: Stop Current Server
Press `Ctrl+C` in the terminal where uvicorn is running.

### Step 2: Restart with Correct Profile

**Option A: Use the start script (easiest)**
```bash
./start_server.sh
```

**Option B: Manual restart**
```bash
export AWS_PROFILE=rise-admin4
export AWS_REGION=us-east-1
export $(cat .env | grep -v '^#' | xargs) 2>/dev/null || true
PYTHONPATH=src uvicorn src.api.main:app --reload --port 8000
```

### Step 3: Test

```bash
curl -X POST http://localhost:8000/api/admin/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "trigger_type": "overdue_balance"
  }'
```

**Expected:** Success response with trigger_id and conversation_id.

---

## Current Status

- ✅ DynamoDB table exists and is accessible
- ✅ AWS credentials work with `rise-admin4` profile  
- ✅ Code is configured correctly
- ⚠️  Server needs restart to pick up new credentials

