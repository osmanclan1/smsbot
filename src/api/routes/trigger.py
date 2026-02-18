"""
Trigger endpoints for initiating conversations.
"""

import csv
import io
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from api.services.sms_service import SMSService
from api.services.voice_service import VoiceService
from api.services.conversation import ConversationEngine
from api.services.trigger_arbitration import should_send_trigger
from storage.dynamodb import DynamoDBService
from api.models.trigger import TriggerRequest, TriggerResponse, CSVUploadResponse

router = APIRouter()


def handle_trigger(event, context):
    """Lambda handler for trigger endpoint."""
    import json
    
    try:
        body = json.loads(event.get('body', '{}'))
        phone_number = body.get('phone_number')
        trigger_type = body.get('trigger_type')
        metadata = body.get('metadata', {})
        channel = body.get('channel', 'sms')  # Default to SMS
        
        if not phone_number or not trigger_type:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'phone_number and trigger_type required'})
            }
        
        db = DynamoDBService()
        engine = ConversationEngine()
        sms_service = SMSService()
        voice_service = VoiceService()
        
        # Create trigger record
        trigger_id = db.create_trigger(phone_number, trigger_type, metadata)
        
        # Get initial message
        initial_message = engine.get_initial_message(trigger_type)
        
        # Create conversation with specified channel
        conversation_id = db.create_conversation(
            phone_number=phone_number,
            trigger_type=trigger_type,
            trigger_id=trigger_id,
            initial_message=initial_message,
            channel=channel
        )
        
        # Update trigger with conversation ID
        db.update_trigger_status(trigger_id, 'sent', conversation_id)
        
        # Send via SMS or Voice based on channel
        message_sent = False
        message_id = None
        call_id = None
        error = None
        
        if channel == 'voice':
            # Initiate voice call
            conversation_context = {
                'conversation_id': conversation_id,
                'trigger_type': trigger_type,
                'initial_message': initial_message
            }
            call_result = voice_service.initiate_call(
                to_phone=phone_number,
                conversation_context=conversation_context
            )
            message_sent = call_result.get('success', False)
            call_id = call_result.get('call_id')
            if not message_sent:
                error = call_result.get('error', 'Unknown error')
        else:
            # Send SMS
            send_result = sms_service.send_sms(phone_number, initial_message)
            message_sent = send_result.get('success', False)
            message_id = send_result.get('message_id')
            if not message_sent:
                error = send_result.get('error', 'Unknown error')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'trigger_id': trigger_id,
                'conversation_id': conversation_id,
                'message_sent': message_sent,
                'status': 'sent',
                'message_id': message_id,
                'call_id': call_id,
                'channel': channel,
                'error': error
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


@router.post("/trigger", response_model=TriggerResponse)
async def trigger_conversation(request: TriggerRequest):
    """
    Manually trigger a conversation with a student.
    """
    try:
        # Check trigger arbitration (cooldowns, priority, suppression)
        should_send, reason = should_send_trigger(
            phone_number=request.phone_number,
            trigger_type=request.trigger_type,
            metadata=request.metadata
        )
        
        if not should_send:
            # Return response indicating trigger was suppressed
            return TriggerResponse(
                trigger_id="",  # No trigger created
                conversation_id="",  # No conversation created
                message_sent=False,
                status='suppressed',
                message_id=None,
                sms_error=reason,
                call_id=None,
                voice_error=None,
                channel=request.channel or 'sms'
            )
        
        db = DynamoDBService()
        engine = ConversationEngine()
        sms_service = SMSService()
        
        # Phase 2: Create or update student profile if metadata provided
        if request.metadata:
            try:
                # Extract student info from metadata
                student_id = request.metadata.get('student_id')
                name = request.metadata.get('name')
                email = request.metadata.get('email')
                program = request.metadata.get('program')
                enrollment_status = request.metadata.get('enrollment_status')
                
                if db.students_table and (student_id or name or email):
                    db.create_or_update_student(
                        phone_number=request.phone_number,
                        student_id=student_id,
                        name=name,
                        email=email,
                        program=program,
                        enrollment_status=enrollment_status,
                        metadata=request.metadata
                    )
            except Exception as e:
                print(f"Note: Could not create/update student profile: {e}")
        
        # Create trigger record
        trigger_id = db.create_trigger(
            request.phone_number,
            request.trigger_type,
            request.metadata
        )
        
        # Get initial message
        initial_message = engine.get_initial_message(request.trigger_type)
        
        # Determine channel (default to SMS if not specified)
        channel = request.channel or 'sms'
        
        # Create conversation
        conversation_id = db.create_conversation(
            phone_number=request.phone_number,
            trigger_type=request.trigger_type,
            trigger_id=trigger_id,
            initial_message=initial_message,
            channel=channel
        )
        
        # Phase 2: Schedule follow-up if appropriate (e.g., 3 days for payment reminders)
        followup_days = None
        if request.trigger_type == 'payment_deadline_7days':
            followup_days = 4  # Follow up in 3 days (7 days -> 3 days left)
        elif request.trigger_type == 'payment_deadline_3days':
            followup_days = 2  # Follow up in 1 day (3 days -> 1 day left)
        elif 'deadline' in request.trigger_type:
            followup_days = 1  # Default: follow up 1 day before
        
        if followup_days and db.followups_table:
            try:
                from datetime import datetime, timedelta
                followup_date = (datetime.utcnow() + timedelta(days=followup_days)).isoformat()
                db.create_followup(
                    phone_number=request.phone_number,
                    followup_date=followup_date,
                    trigger_type=f"{request.trigger_type}_reminder",
                    conversation_id=conversation_id,
                    metadata={'original_trigger_id': trigger_id}
                )
            except Exception as e:
                print(f"Note: Could not schedule follow-up: {e}")
        
        # Update trigger with conversation ID
        db.update_trigger_status(trigger_id, 'sent', conversation_id)
        
        # Send via SMS or Voice based on channel
        message_sent = False
        message_id = None
        sms_error = None
        call_id = None
        voice_error = None
        
        if channel == 'voice':
            # Initiate voice call
            voice_service = VoiceService()
            conversation_context = {
                'conversation_id': conversation_id,
                'trigger_type': request.trigger_type,
                'initial_message': initial_message
            }
            call_result = voice_service.initiate_call(
                to_phone=request.phone_number,
                conversation_context=conversation_context
            )
            message_sent = call_result.get('success', False)
            call_id = call_result.get('call_id')
            if not message_sent:
                voice_error = call_result.get('error', 'Unknown error')
                print(f"Failed to initiate voice call to {request.phone_number}: {voice_error}")
        else:
            # Send SMS (phone number normalization handled by SMSService)
            send_result = sms_service.send_sms(request.phone_number, initial_message)
            message_sent = send_result.get('success', False)
            message_id = send_result.get('message_id')
            if not message_sent:
                sms_error = send_result.get('error', 'Unknown error')
                print(f"Failed to send SMS to {request.phone_number}: {sms_error}")
        
        return TriggerResponse(
            trigger_id=trigger_id,
            conversation_id=conversation_id,
            message_sent=message_sent,
            status='sent',
            message_id=message_id,
            sms_error=sms_error,
            call_id=call_id,
            voice_error=voice_error,
            channel=channel
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/csv", response_model=CSVUploadResponse)
async def trigger_csv_upload(
    file: UploadFile = File(...),
    trigger_type: str = Form(...),
    channel: str = Form('sms')
):
    """
    Upload CSV file to trigger multiple conversations.
    
    CSV format:
    phone_number,metadata (optional JSON)
    +1234567890,{"balance": 1500}
    +0987654321,
    """
    try:
        # Read CSV file
        content = await file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        db = DynamoDBService()
        engine = ConversationEngine()
        sms_service = SMSService()
        voice_service = VoiceService()
        
        trigger_ids = []
        successful = 0
        failed = 0
        
        for row in csv_reader:
            try:
                phone_number = row.get('phone_number', '').strip()
                if not phone_number:
                    failed += 1
                    continue
                
                # Parse metadata if provided
                metadata = {}
                if 'metadata' in row and row['metadata']:
                    try:
                        import json
                        metadata = json.loads(row['metadata'])
                    except:
                        pass
                
                # Merge any other columns as metadata
                for key, value in row.items():
                    if key not in ['phone_number', 'metadata'] and value:
                        metadata[key] = value
                
                # Phase 2: Create or update student profile if metadata provided
                if metadata and db.students_table:
                    try:
                        student_id = metadata.get('student_id')
                        name = metadata.get('name')
                        email = metadata.get('email')
                        program = metadata.get('program')
                        enrollment_status = metadata.get('enrollment_status')
                        
                        if student_id or name or email:
                            db.create_or_update_student(
                                phone_number=phone_number,
                                student_id=student_id,
                                name=name,
                                email=email,
                                program=program,
                                enrollment_status=enrollment_status,
                                metadata=metadata
                            )
                    except Exception as e:
                        print(f"Note: Could not create/update student profile for {phone_number}: {e}")
                
                # Create trigger
                trigger_id = db.create_trigger(phone_number, trigger_type, metadata)
                
                # Get initial message
                initial_message = engine.get_initial_message(trigger_type)
                
                # Create conversation
                conversation_id = db.create_conversation(
                    phone_number=phone_number,
                    trigger_type=trigger_type,
                    trigger_id=trigger_id,
                    initial_message=initial_message,
                    channel=channel
                )
                
                # Phase 2: Schedule follow-up if appropriate
                followup_days = None
                if trigger_type == 'payment_deadline_7days':
                    followup_days = 4
                elif trigger_type == 'payment_deadline_3days':
                    followup_days = 2
                elif 'deadline' in trigger_type:
                    followup_days = 1
                
                if followup_days and db.followups_table:
                    try:
                        from datetime import datetime, timedelta
                        followup_date = (datetime.utcnow() + timedelta(days=followup_days)).isoformat()
                        db.create_followup(
                            phone_number=phone_number,
                            followup_date=followup_date,
                            trigger_type=f"{trigger_type}_reminder",
                            conversation_id=conversation_id,
                            metadata={'original_trigger_id': trigger_id}
                        )
                    except Exception as e:
                        print(f"Note: Could not schedule follow-up for {phone_number}: {e}")
                
                # Update trigger
                db.update_trigger_status(trigger_id, 'sent', conversation_id)
                
                # Send via SMS or Voice based on channel
                if channel == 'voice':
                    conversation_context = {
                        'conversation_id': conversation_id,
                        'trigger_type': trigger_type,
                        'initial_message': initial_message
                    }
                    call_result = voice_service.initiate_call(
                        to_phone=phone_number,
                        conversation_context=conversation_context
                    )
                    if call_result.get('success'):
                        successful += 1
                    else:
                        failed += 1
                        print(f"Failed to initiate voice call to {phone_number}: {call_result.get('error', 'Unknown error')}")
                else:
                    # Send SMS (phone number normalization handled by SMSService)
                    send_result = sms_service.send_sms(phone_number, initial_message)
                    if send_result.get('success'):
                        successful += 1
                    else:
                        failed += 1
                        print(f"Failed to send SMS to {phone_number}: {send_result.get('error', 'Unknown error')}")
                
                trigger_ids.append(trigger_id)
                
            except Exception as e:
                print(f"Error processing row: {e}")
                failed += 1
                continue
        
        return CSVUploadResponse(
            triggers_created=len(trigger_ids),
            successful=successful,
            failed=failed,
            trigger_ids=trigger_ids
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

