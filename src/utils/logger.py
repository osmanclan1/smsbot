"""
Result logger - finish() function to log conversation outcomes.
"""

from typing import Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.dynamodb import DynamoDBService


def finish(
    conversation_id: str,
    result_type: str,
    phone_number: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> str:
    """
    Log conversation outcome to DynamoDB Results table.
    This function is called when a conversation completes.
    
    Args:
        conversation_id: ID of the completed conversation
        result_type: Type of result:
            - "paid": Student completed payment
            - "registered": Student completed registration
            - "resolved": Issue was resolved
            - "reminder_sent": Reminder was successfully delivered (Phase 1)
            - "escalated": Case needs human intervention
            - "no_response": Student didn't respond
            - "abandoned": Conversation was abandoned
        phone_number: Student phone number (optional)
        metadata: Additional metadata about the result (optional)
        
    Returns:
        Result ID
        
    Example:
        finish(
            conversation_id="abc123",
            result_type="paid",
            phone_number="+1234567890",
            metadata={"amount": 1500, "payment_method": "credit_card"}
        )
    """
    db = DynamoDBService()
    
    # Update conversation status to completed
    db.update_conversation_status(conversation_id, 'completed')
    
    # Create result record
    result_id = db.create_result(
        conversation_id=conversation_id,
        result_type=result_type,
        phone_number=phone_number,
        metadata=metadata or {}
    )
    
    return result_id

