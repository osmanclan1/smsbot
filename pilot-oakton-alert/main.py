"""
Oakton Alert pilot – FastAPI app.
Run from this directory: uvicorn main:app --reload --port 8001
"""
from pathlib import Path

from dotenv import load_dotenv

# Load project root .env so TELNYX_* and OAKTON_ALERT_* are available
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

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
