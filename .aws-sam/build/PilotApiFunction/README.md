# Oakton Alert pilot v1

This is the **active** pilot package. The original [`pilot-oakton-alert/`](../pilot-oakton-alert/) directory is kept as a **frozen** copy for reference.

## What is different in v1

- **DynamoDB** (`PILOT_DYNAMODB_TABLE`) for durable opt-out when running in AWS.
- **S3 → ingest Lambda → SQS → sender Lambda** for roster-driven SMS (see [`docs/PILOT_ARCHITECTURE_V1.md`](../docs/PILOT_ARCHITECTURE_V1.md)).
- SAM template: [`deploy/template-pilot.yaml`](../deploy/template-pilot.yaml) (functions `smsbot-pilot-v1-api`, `smsbot-pilot-v1-ingest`, `smsbot-pilot-v1-sender`).

## Run locally

```bash
cd pilot-v1
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Without `PILOT_DYNAMODB_TABLE`, opt-out storage is **in-memory** (development only).

## Deploy

From repo root:

```bash
./deploy/deploy-pilot.sh
```

## Tests

```bash
pytest tests/
```
