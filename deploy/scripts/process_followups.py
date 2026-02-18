#!/usr/bin/env python3
"""
Script to process due follow-ups.
Run periodically (e.g., hourly) to send follow-up messages.
"""

import sys
import os

# Add src directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from storage.dynamodb import DynamoDBService
from api.services.conversation import ConversationEngine
from api.services.sms_service import SMSService


def process_followups():
    """Process and send due follow-ups."""
    print("Checking for due follow-ups...")
    
    db = DynamoDBService()
    
    if not db.followups_table:
        print("ERROR: Followups table does not exist. Please create it first.")
        return False
    
    # Get due follow-ups
    due_followups = db.get_due_followups(limit=100)
    
    if not due_followups:
        print("No due follow-ups found.")
        return True
    
    print(f"Found {len(due_followups)} due follow-ups")
    
    engine = ConversationEngine()
    sms_service = SMSService()
    
    sent_count = 0
    failed_count = 0
    
    for followup in due_followups:
        try:
            phone_number = followup['phone_number']
            trigger_type = followup.get('trigger_type', 'default')
            followup_id = followup['followup_id']
            
            # Get initial message for this trigger type
            initial_message = engine.get_initial_message(trigger_type)
            
            # Create conversation
            conversation_id = db.create_conversation(
                phone_number=phone_number,
                trigger_type=f"followup_{trigger_type}",
                initial_message=initial_message
            )
            
            # Send message
            send_result = sms_service.send_sms(phone_number, initial_message)
            
            if send_result.get('success'):
                # Update follow-up status
                db.update_followup_status(
                    followup_id=followup_id,
                    status='sent',
                    conversation_id=conversation_id
                )
                sent_count += 1
                print(f"✓ Sent follow-up to {phone_number}")
            else:
                failed_count += 1
                print(f"✗ Failed to send follow-up to {phone_number}: {send_result.get('error')}")
                
        except Exception as e:
            failed_count += 1
            print(f"✗ Error processing follow-up {followup.get('followup_id', 'unknown')}: {e}")
    
    print(f"\nCompleted: {sent_count} sent, {failed_count} failed")
    return True


if __name__ == "__main__":
    success = process_followups()
    sys.exit(0 if success else 1)

