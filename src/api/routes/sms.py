"""
SMS webhook handler for Telnyx incoming messages.
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from api.services.sms_service import SMSService
from api.services.conversation import ConversationEngine


router = APIRouter()


def handle_webhook(event, context):
    """
    Lambda handler for Telnyx webhook.
    
    Telnyx webhook payload structure:
    {
        "data": {
            "event_type": "message.received",
            "payload": {
                "from": {"phone_number": "+1234567890"},
                "to": [{"phone_number": "+0987654321"}],
                "text": "Hello",
                ...
            }
        }
    }
    """
    try:
        # Parse event body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Handle Telnyx webhook format
        event_data = body.get('data', {})
        event_type = event_data.get('event_type')
        payload = event_data.get('payload', {})
        
        if event_type != 'message.received':
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Event type not handled'})
            }
        
        # Extract phone number and message
        from_number = payload.get('from', {}).get('phone_number')
        if not from_number:
            # Try alternative format
            from_number = payload.get('from')
            if isinstance(from_number, dict):
                from_number = from_number.get('phone_number')
        
        message_text = payload.get('text', '')
        
        if not from_number or not message_text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing phone number or message'})
            }
        
        # Process message through conversation engine
        engine = ConversationEngine()
        result = engine.process_message(from_number, message_text)
        
        # Send response via SMS
        sms_service = SMSService()
        to_phone = payload.get('to', [{}])[0].get('phone_number') or from_number
        
        # Don't send response if conversation finished
        if result.get('action') != 'finish':
            response_text = result.get('response', '')
            if response_text:
                sms_service.send_sms(to_phone, response_text)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'success': True})
        }
        
    except Exception as e:
        print(f"Error handling webhook: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


@router.post("/webhook")
async def webhook_handler(request: Request):
    """
    FastAPI endpoint for Telnyx webhook.
    """
    try:
        body = await request.json()
        
        # Handle Telnyx webhook format
        event_data = body.get('data', {})
        event_type = event_data.get('event_type')
        payload = event_data.get('payload', {})
        
        if event_type != 'message.received':
            return {"message": "Event type not handled"}
        
        # Extract phone number and message
        from_number = payload.get('from', {}).get('phone_number')
        if not from_number:
            from_number = payload.get('from')
            if isinstance(from_number, dict):
                from_number = from_number.get('phone_number')
        
        message_text = payload.get('text', '')
        
        if not from_number or not message_text:
            raise HTTPException(status_code=400, detail="Missing phone number or message")
        
        # Process message
        engine = ConversationEngine()
        result = engine.process_message(from_number, message_text)
        
        # Send response via SMS
        sms_service = SMSService()
        to_phone = payload.get('to', [{}])[0].get('phone_number') if payload.get('to') else from_number
        
        # Don't send response if conversation finished
        if result.get('action') != 'finish':
            response_text = result.get('response', '')
            if response_text:
                sms_service.send_sms(to_phone, response_text)
        
        return {"success": True}
        
    except Exception as e:
        print(f"Error handling webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

