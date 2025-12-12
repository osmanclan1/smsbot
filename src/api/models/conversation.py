"""
Data models for conversations.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class Message(BaseModel):
    """Message model."""
    role: str
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    """Response model for conversation."""
    conversation_id: str
    phone_number: str
    created_at: str
    updated_at: str
    status: str
    messages: List[Message]
    trigger_type: Optional[str] = None
    trigger_id: Optional[str] = None


class ConversationListResponse(BaseModel):
    """Response model for conversation list."""
    conversations: List[ConversationResponse]
    total: int
    last_key: Optional[str] = None

