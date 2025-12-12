"""
Student API endpoints for authenticated students.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from api.routes.student_auth import require_student_auth
from starlette.requests import Request
from api.services.conversation import ConversationEngine
from storage.dynamodb import DynamoDBService

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None


@router.post("/chat")
async def send_message(
    request: Request,
    chat_data: ChatMessage,
    student_info: dict = Depends(require_student_auth)
):
    """
    Send a message to the bot (web-based chat for authenticated students).
    """
    try:
        username = student_info["username"]
        student_id = student_info["student_id"]
        
        # Get or create conversation for this student
        db = DynamoDBService()
        
        # For web-based students, use username as identifier instead of phone number
        # Create a virtual phone number format: "WEB:username"
        virtual_phone = f"WEB:{username}"
        
        # Get or create conversation
        conversation = db.get_conversation_by_phone(virtual_phone)
        
        if not conversation:
            # Create new conversation
            conversation_id = db.create_conversation(
                phone_number=virtual_phone,
                trigger_type="web_chat"
            )
        else:
            conversation_id = conversation.get('conversation_id')
        
        # Process message
        engine = ConversationEngine()
        result = engine.generate_response(
            conversation_id=conversation_id,
            user_message=chat_data.message,
            phone_number=virtual_phone  # Virtual phone for web students
        )
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "response": result.get('response', ''),
            "action": result.get('action', 'continue')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def get_conversations(
    request: Request,
    student_info: dict = Depends(require_student_auth)
):
    """
    Get conversation history for the authenticated student.
    """
    try:
        username = student_info["username"]
        virtual_phone = f"WEB:{username}"
        
        db = DynamoDBService()
        conversations = db.get_conversations_by_phone(virtual_phone, limit=50)
        
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile")
async def get_profile(
    request: Request,
    student_info: dict = Depends(require_student_auth)
):
    """
    Get student profile information.
    """
    try:
        username = student_info["username"]
        
        db = DynamoDBService()
        student = db.get_student_by_username(username)
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Return profile without sensitive data
        return {
            "username": student.get("username"),
            "name": student.get("name"),
            "email": student.get("email"),
            "student_id": student.get("student_id"),
            "created_at": student.get("created_at")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
