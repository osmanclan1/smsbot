"""
Oakton Alert pilot – FastAPI app.
Run from this directory: uvicorn main:app --reload --port 8001
Deploy: sam build -t deploy/template-pilot.yaml && sam deploy
"""
import os
from pathlib import Path

# Load .env only when not in Lambda (Lambda gets env from stack/template)
if not os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    try:
        from dotenv import load_dotenv
        _env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(_env_path)
    except ImportError:
        pass

from fastapi import FastAPI

from webhook import router as webhook_router
from trigger import router as trigger_router

app = FastAPI(title="Oakton Alert Pilot", version="1.0.0")

app.include_router(webhook_router, prefix="/api/sms", tags=["sms"])
app.include_router(trigger_router, prefix="/api", tags=["trigger"])


@app.get("/")
async def root():
    return {"service": "Oakton Alert Pilot", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Lambda handler using Mangum (for AWS SAM deploy)
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = None  # local uvicorn does not use handler
