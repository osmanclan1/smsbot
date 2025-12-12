# Force Server Restart Required

The server needs to be **completely restarted** (not just reloaded) to pick up the AWS profile configuration.

## Steps:

1. **Find and kill the server process:**
   ```bash
   # Find the process
   ps aux | grep uvicorn | grep -v grep
   
   # Kill it (replace PID with actual process ID)
   kill <PID>
   # Or kill all uvicorn processes:
   pkill -f uvicorn
   ```

2. **Start fresh:**
   ```bash
   ./start_server.sh
   ```

   Or manually:
   ```bash
   export AWS_PROFILE=rise-admin4
   export AWS_REGION=us-east-1
   export $(cat .env | grep -v '^#' | xargs) 2>/dev/null || true
   PYTHONPATH=src uvicorn src.api.main:app --reload --port 8000
   ```

3. **Test:**
   ```bash
   curl -X POST http://localhost:8000/api/admin/trigger \
     -H "Content-Type: application/json" \
     -d '{
       "phone_number": "+1234567890",
       "trigger_type": "overdue_balance"
     }'
   ```

The issue is that uvicorn's auto-reload doesn't always reinitialize boto3 sessions properly. A full restart is needed.

