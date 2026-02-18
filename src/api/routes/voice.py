"""
Voice webhook handler for Telnyx Voice AI Agent.
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Optional
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from api.services.conversation import ConversationEngine
from storage.dynamodb import DynamoDBService


router = APIRouter()


def _normalize_phone(phone: str) -> str:
    """
    Normalize phone number to E.164 format.
    
    Args:
        phone: Phone number in various formats
        
    Returns:
        Phone number in E.164 format (e.g., +1234567890)
    """
    if not phone:
        return phone
    
    phone = phone.strip()
    # Remove any spaces, dashes, parentheses
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('.', '')
    
    # If it already starts with +, return as is
    if phone.startswith('+'):
        return phone
    
    # Handle US numbers
    if phone.startswith('1') and len(phone) == 11:
        return '+' + phone
    elif len(phone) == 10:
        return '+1' + phone
    elif len(phone) == 11 and phone[0] == '1':
        return '+' + phone
    else:
        cleaned = phone.lstrip('1')
        if len(cleaned) == 10:
            return '+1' + cleaned
        return '+1' + phone


@router.post("/webhook")
async def voice_webhook_handler(request: Request):
    """
    FastAPI endpoint for Telnyx Voice AI Agent webhook.
    
    Expected payload formats (Telnyx Voice AI Agent may send different formats):
    1. Direct format:
       {
           "transcript": "user speech text",
           "caller_id": "+1234567890",
           "conversation_id": "telnyx-conv-id",
           "call_id": "call-id"
       }
    
    2. Nested format:
       {
           "data": {
               "transcript": "user speech text",
               "caller": {"phone_number": "+1234567890"},
               "conversation_id": "telnyx-conv-id"
           }
       }
    
    3. Webhook tool format (when using Webhook tool in agent):
       {
           "user_message": "transcribed text",
           "phone_number": "+1234567890",
           "call_id": "call-id"
       }
    """
    try:
        body = await request.json()
        
        # Try to extract transcript and phone number from various payload formats
        transcript = None
        phone_number = None
        call_id = None
        telnyx_conversation_id = None
        
        # Format 1: Direct format
        if 'transcript' in body:
            transcript = body.get('transcript', '').strip()
            phone_number = body.get('caller_id') or body.get('phone_number') or body.get('caller')
            if isinstance(phone_number, dict):
                phone_number = phone_number.get('phone_number')
            call_id = body.get('call_id')
            telnyx_conversation_id = body.get('conversation_id')
        
        # Format 2: Nested format
        elif 'data' in body:
            data = body.get('data', {})
            transcript = data.get('transcript', '').strip()
            caller = data.get('caller')
            if isinstance(caller, dict):
                phone_number = caller.get('phone_number')
            else:
                phone_number = caller
            call_id = data.get('call_id')
            telnyx_conversation_id = data.get('conversation_id')
        
        # Format 3: Webhook tool format
        elif 'user_message' in body:
            transcript = body.get('user_message', '').strip()
            phone_number = body.get('phone_number')
            call_id = body.get('call_id')
        
        # Format 4: Alternative field names
        else:
            transcript = body.get('message') or body.get('text') or body.get('input', '').strip()
            phone_number = body.get('from') or body.get('caller_id') or body.get('phone_number')
            if isinstance(phone_number, dict):
                phone_number = phone_number.get('phone_number')
            call_id = body.get('call_id')
            telnyx_conversation_id = body.get('conversation_id')
        
        # Validate required fields
        if not phone_number:
            raise HTTPException(status_code=400, detail="Missing phone number in webhook payload")
        
        # Normalize phone number
        phone_number = _normalize_phone(phone_number)
        
        print(f"Processing voice message from {phone_number}: {transcript[:50] if transcript else '(empty/initial call)'}...")
        
        # Process message through conversation engine
        engine = ConversationEngine()
        db = DynamoDBService()
        
        # Find or create conversation (shared with SMS)
        conversation = db.get_conversation_by_phone(phone_number)
        
        if not conversation:
            # Create new conversation
            conversation_id = db.create_conversation(
                phone_number=phone_number,
                channel='voice'
            )
            conversation = db.get_conversation(conversation_id)
        else:
            conversation_id = conversation.get('conversation_id')
            # Update channel to 'both' if it was 'sms' only
            current_channel = conversation.get('channel', 'sms')
            if current_channel == 'sms':
                try:
                    if db.conversations_table:
                        db.conversations_table.update_item(
                            Key={'conversation_id': conversation_id},
                            UpdateExpression='SET #channel = :channel',
                            ExpressionAttributeNames={'#channel': 'channel'},
                            ExpressionAttributeValues={':channel': 'both'}
                        )
                except Exception as e:
                    print(f"Note: Could not update channel: {e}")
        
        # Check if this is a new triggered conversation (no user messages yet)
        # If so, and there's an initial message, we should return that first
        messages = conversation.get('messages', [])
        user_messages = [m for m in messages if m.get('role') == 'user']
        is_new_triggered_call = len(user_messages) == 0 and conversation.get('trigger_type')
        
        if is_new_triggered_call and not transcript:
            # This is likely the call being answered - return the initial trigger message
            initial_message = None
            # Check if initial message is already in conversation
            assistant_messages = [m for m in messages if m.get('role') == 'assistant']
            if assistant_messages:
                initial_message = assistant_messages[0].get('content')
            else:
                # Get initial message from trigger type
                initial_message = engine.get_initial_message(conversation.get('trigger_type'))
                # Add the initial message to conversation
                if initial_message:
                    db.add_message(conversation_id, 'assistant', initial_message, channel='voice')
            
            if initial_message:
                return {
                    "response": initial_message,
                    "conversation_id": conversation_id,
                    "call_id": call_id
                }
        
        if not transcript:
            # Empty transcript for non-triggered calls - return a default greeting
            print(f"Received empty transcript from {phone_number} (call_id: {call_id})")
            return {
                "response": "I'm here to help! What can I assist you with today?",
                "conversation_id": conversation_id
            }
        
        # Generate response using conversation engine
        result = engine.generate_response(
            conversation_id=conversation_id,
            user_message=transcript,
            phone_number=phone_number,
            channel='voice'
        )
        
        response_text = result.get('response', '')
        
        # Return response for Telnyx Voice AI Agent to speak
        return {
            "response": response_text,
            "conversation_id": conversation_id,
            "action": result.get('action'),
            "call_id": call_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error handling voice webhook: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def voice_health():
    """Health check endpoint for voice service."""
    return {"status": "healthy", "service": "voice"}

