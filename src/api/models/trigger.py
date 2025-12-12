"""
Data models for triggers.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class TriggerRequest(BaseModel):
    """Request model for manual trigger."""
    phone_number: str = Field(..., description="Student phone number (E.164 format)")
    trigger_type: str = Field(
        ...,
        description="Type of trigger. Options: overdue_balance, not_registered, upcoming_deadline, hold_on_account, payment_deadline_7days, payment_deadline_3days, payment_deadline_1day, registration_opens, class_starts_soon, drop_deadline_warning, financial_aid_deadline, advising_reminder, graduation_checklist"
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class TriggerResponse(BaseModel):
    """Response model for trigger."""
    trigger_id: str
    conversation_id: str
    message_sent: bool
    status: str


class CSVUploadResponse(BaseModel):
    """Response model for CSV upload."""
    triggers_created: int
    successful: int
    failed: int
    trigger_ids: list[str]

