"""
Admin API endpoints for viewing conversations, triggers, and results.
"""

import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from storage.dynamodb import DynamoDBService
from api.models.conversation import ConversationResponse, ConversationListResponse, Message

router = APIRouter()


def handle_request(event, context):
    """Lambda handler for admin API."""
    try:
        path = event.get('path', '')
        method = event.get('httpMethod', 'GET')
        
        db = DynamoDBService()
        
        if path == '/api/admin/conversations' and method == 'GET':
            # List conversations
            limit = int(event.get('queryStringParameters', {}).get('limit', 50))
            conversations_data = db.list_conversations(limit=limit)
            
            conversations = []
            for conv in conversations_data['conversations']:
                conversations.append({
                    'conversation_id': conv['conversation_id'],
                    'phone_number': conv['phone_number'],
                    'created_at': conv['created_at'],
                    'updated_at': conv['updated_at'],
                    'status': conv['status'],
                    'messages': conv.get('messages', []),
                    'trigger_type': conv.get('trigger_type'),
                    'trigger_id': conv.get('trigger_id')
                })
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'conversations': conversations,
                    'total': len(conversations),
                    'last_key': conversations_data.get('last_key')
                })
            }
        
        elif path.startswith('/api/admin/conversations/') and method == 'GET':
            # Get conversation detail
            conversation_id = path.split('/')[-1]
            conversation = db.get_conversation(conversation_id)
            
            if not conversation:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Conversation not found'})
                }
            
            return {
                'statusCode': 200,
                'body': json.dumps(conversation)
            }
        
        elif path == '/api/admin/results' and method == 'GET':
            # List results
            limit = int(event.get('queryStringParameters', {}).get('limit', 50))
            results = db.list_results(limit=limit)
            
            return {
                'statusCode': 200,
                'body': json.dumps({'results': results, 'total': len(results)})
            }
        
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    last_key: Optional[str] = Query(None)
):
    """List all conversations."""
    try:
        db = DynamoDBService()
        
        # Convert last_key string back to dict if provided
        last_key_dict = None
        if last_key:
            try:
                last_key_dict = json.loads(last_key)
            except:
                pass
        
        conversations_data = db.list_conversations(limit=limit, last_key=last_key_dict)
        
        conversations = []
        for conv in conversations_data['conversations']:
            messages = [
                Message(**msg) for msg in conv.get('messages', [])
            ]
            conversations.append(ConversationResponse(
                conversation_id=conv['conversation_id'],
                phone_number=conv['phone_number'],
                created_at=conv['created_at'],
                updated_at=conv['updated_at'],
                status=conv['status'],
                messages=messages,
                trigger_type=conv.get('trigger_type'),
                trigger_id=conv.get('trigger_id')
            ))
        
        return ConversationListResponse(
            conversations=conversations,
            total=len(conversations),
            last_key=json.dumps(conversations_data.get('last_key')) if conversations_data.get('last_key') else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get conversation details including full transcript."""
    try:
        db = DynamoDBService()
        conversation = db.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = [
            Message(**msg) for msg in conversation.get('messages', [])
        ]
        
        return ConversationResponse(
            conversation_id=conversation['conversation_id'],
            phone_number=conversation['phone_number'],
            created_at=conversation['created_at'],
            updated_at=conversation['updated_at'],
            status=conversation['status'],
            messages=messages,
            trigger_type=conversation.get('trigger_type'),
            trigger_id=conversation.get('trigger_id')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results")
async def list_results(limit: int = Query(50, ge=1, le=100)):
    """List all results."""
    try:
        db = DynamoDBService()
        results = db.list_results(limit=limit)
        
        return {
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/triggers")
async def list_triggers(limit: int = Query(50, ge=1, le=100)):
    """List all triggers."""
    try:
        db = DynamoDBService()
        triggers = db.list_triggers(limit=limit)
        
        return {
            "triggers": triggers,
            "total": len(triggers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-chat")
async def test_chat(request: dict):
    """
    Test endpoint for chatting with the bot.
    Doesn't send actual SMS, just simulates a conversation.
    """
    try:
        from api.services.conversation import ConversationEngine
        
        phone_number = request.get("phone_number", "+15555551234")  # Test number
        message = request.get("message")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        engine = ConversationEngine()
        result = engine.process_message(phone_number, message)
        
        return {
            "response": result.get("response", ""),
            "action": result.get("action", ""),
            "result_type": result.get("result_type")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

