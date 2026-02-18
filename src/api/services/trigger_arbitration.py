"""
Trigger arbitration service - handles cooldowns, priority, and suppression.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from storage.dynamodb import DynamoDBService
from typing import Dict, Optional, Tuple


# Trigger priority (higher = more important)
TRIGGER_PRIORITY = {
    'payment_deadline_1day': 100,
    'hold_on_account': 90,
    'overdue_balance': 85,
    'payment_deadline_3days': 70,
    'payment_deadline_7days': 60,
    'registration_opens': 50,
    'class_starts_soon': 45,
    'not_registered': 40,
    'drop_deadline_warning': 35,
    'financial_aid_deadline': 35,
    'advising_reminder': 30,
    'graduation_checklist': 25,
    'upcoming_deadline': 20,
    'registration_opens': 15,
}

# Cooldown periods (hours) - how long to wait before sending another trigger
TRIGGER_COOLDOWN = {
    'payment_deadline_1day': 24,
    'payment_deadline_3days': 72,
    'payment_deadline_7days': 168,  # 7 days
    'hold_on_account': 48,
    'overdue_balance': 72,
    'not_registered': 96,
    'registration_opens': 168,
    'class_starts_soon': 72,
    'drop_deadline_warning': 48,
    'financial_aid_deadline': 72,
    'advising_reminder': 168,
    'graduation_checklist': 168,
    'upcoming_deadline': 72,
}

# Blocking relationships - if active conversation is about X, don't send trigger Y
TRIGGER_BLOCKS = {
    'hold_on_account': ['not_registered', 'registration_opens'],
    'overdue_balance': ['not_registered', 'registration_opens'],
    'payment_deadline_1day': ['payment_deadline_3days', 'payment_deadline_7days', 'not_registered'],
    'payment_deadline_3days': ['payment_deadline_7days'],
}


def get_trigger_priority(trigger_type: str) -> int:
    """Get priority for a trigger type."""
    return TRIGGER_PRIORITY.get(trigger_type, 10)


def get_trigger_cooldown(trigger_type: str) -> int:
    """Get cooldown period (hours) for a trigger type."""
    return TRIGGER_COOLDOWN.get(trigger_type, 72)  # Default 72 hours


def should_send_trigger(
    phone_number: str,
    trigger_type: str,
    metadata: Optional[Dict] = None
) -> Tuple[bool, Optional[str]]:
    """
    Determine if a trigger should be sent based on cooldowns, priority, and active conversations.
    
    Args:
        phone_number: Student phone number
        trigger_type: Type of trigger to send
        metadata: Optional trigger metadata
        
    Returns:
        Tuple of (should_send: bool, reason: Optional[str])
        If should_send is False, reason explains why
    """
    db = DynamoDBService()
    
    # Check if student is opted out
    if db.is_student_opted_out(phone_number):
        return False, "Student has opted out of SMS communications"
    
    # Check cooldown - get recent triggers for this phone number
    cooldown_hours = get_trigger_cooldown(trigger_type)
    recent_triggers = db.get_recent_triggers(phone_number, hours=cooldown_hours)
    
    # Check if we've sent this trigger type recently
    for trigger in recent_triggers:
        if trigger.get('trigger_type') == trigger_type:
            return False, f"Trigger '{trigger_type}' sent recently (within {cooldown_hours} hours)"
    
    # Check for active conversation
    active_conv = db.get_active_conversation(phone_number)
    if active_conv:
        # Get current trigger type from active conversation
        current_trigger_type = active_conv.get('trigger_type')
        current_flow = active_conv.get('active_flow')
        current_state = active_conv.get('conversation_state', active_conv.get('status', 'active'))
        
        # Don't send new triggers if conversation is in critical flow or terminal state
        if current_state in {'RESOLVED', 'ESCALATED', 'TIMEOUT'}:
            # Terminal state - allow new triggers
            pass
        elif current_flow in {'payment', 'hold_diagnosis'} and trigger_type not in {'hold_on_account', 'overdue_balance'}:
            # Critical flow active - only allow related triggers
            return False, f"Active conversation in critical flow '{current_flow}' - suppressing unrelated triggers"
        
        # Check blocking relationships
        blocked_triggers = TRIGGER_BLOCKS.get(current_trigger_type, [])
        if trigger_type in blocked_triggers:
            return False, f"Trigger '{trigger_type}' blocked by active conversation with trigger '{current_trigger_type}'"
        
        # Check priority - don't send lower priority triggers if higher priority conversation is active
        current_priority = get_trigger_priority(current_trigger_type or 'default')
        new_priority = get_trigger_priority(trigger_type)
        
        if new_priority < current_priority:
            return False, f"Trigger '{trigger_type}' (priority {new_priority}) is lower than active conversation (priority {current_priority})"
    
    # All checks passed - send the trigger
    return True, None
