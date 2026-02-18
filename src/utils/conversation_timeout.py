"""
Conversation timeout service - automatically transitions conversations to TIMEOUT after inactivity.
"""
import os
import sys
from typing import List, Optional
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.dynamodb import DynamoDBService


class ConversationTimeoutService:
    """Service for handling conversation timeouts after inactivity."""
    
    # Default timeout periods (hours)
    DEFAULT_TIMEOUT_HOURS = 72  # 3 days
    
    # Timeout periods by conversation state
    STATE_TIMEOUTS = {
        'INIT': 24,  # 24 hours if never responded
        'AWAITING_USER': 72,  # 3 days if waiting for user
        'IN_FLOW': 168,  # 7 days if in active flow (more lenient)
    }
    
    def __init__(self, timeout_hours: Optional[int] = None):
        """
        Initialize timeout service.
        
        Args:
            timeout_hours: Default timeout in hours (default from env or 72)
        """
        self.timeout_hours = int(os.getenv(
            'CONVERSATION_TIMEOUT_HOURS',
            timeout_hours or self.DEFAULT_TIMEOUT_HOURS
        ))
        self.db = DynamoDBService()
    
    def check_and_timeout_conversations(self, limit: int = 100) -> List[str]:
        """
        Check for timed-out conversations and transition them to TIMEOUT state.
        
        Args:
            limit: Maximum number of conversations to check per run
            
        Returns:
            List of conversation IDs that were timed out
        """
        timed_out_ids = []
        
        try:
            # Get active conversations (non-terminal states)
            conversations = self.db.list_conversations(limit=limit)
            
            now = datetime.utcnow()
            
            for conversation in conversations.get('conversations', []):
                conversation_id = conversation.get('conversation_id')
                state = conversation.get('conversation_state', conversation.get('status', 'active'))
                
                # Skip terminal states
                if state in {'RESOLVED', 'ESCALATED', 'TIMEOUT'}:
                    continue
                
                # Determine timeout period based on state
                timeout_hours = self.STATE_TIMEOUTS.get(state, self.timeout_hours)
                
                # Get last activity timestamp
                last_activity = self._get_last_activity(conversation)
                if not last_activity:
                    continue
                
                # Check if timed out
                time_since_activity = now - last_activity
                if time_since_activity >= timedelta(hours=timeout_hours):
                    # Timeout this conversation
                    self.db.transition_conversation_state(
                        conversation_id,
                        'TIMEOUT',
                        reason=f'No activity for {int(time_since_activity.total_seconds() / 3600)} hours (timeout: {timeout_hours}h)'
                    )
                    timed_out_ids.append(conversation_id)
                    print(f"⏰ Conversation {conversation_id} timed out after {int(time_since_activity.total_seconds() / 3600)} hours")
        
        except Exception as e:
            print(f"Error checking conversation timeouts: {e}")
        
        return timed_out_ids
    
    def _get_last_activity(self, conversation: dict) -> Optional[datetime]:
        """Get last activity timestamp from conversation."""
        messages = conversation.get('messages', [])
        if not messages:
            # No messages - use conversation creation time
            created_at_str = conversation.get('created_at')
            if created_at_str:
                try:
                    return datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except:
                    pass
            return None
        
        # Get most recent message timestamp
        last_message = messages[-1]
        timestamp_str = last_message.get('timestamp')
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                pass
        
        # Fallback to conversation updated_at
        updated_at_str = conversation.get('updated_at')
        if updated_at_str:
            try:
                return datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
            except:
                pass
        
        return None
    
    def should_timeout_conversation(self, conversation_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if a specific conversation should be timed out.
        
        Args:
            conversation_id: Conversation ID to check
            
        Returns:
            Tuple of (should_timeout: bool, reason: Optional[str])
        """
        conversation = self.db.get_conversation(conversation_id)
        if not conversation:
            return False, "Conversation not found"
        
        state = conversation.get('conversation_state', conversation.get('status', 'active'))
        
        # Skip terminal states
        if state in {'RESOLVED', 'ESCALATED', 'TIMEOUT'}:
            return False, f"Conversation already in terminal state: {state}"
        
        # Determine timeout period
        timeout_hours = self.STATE_TIMEOUTS.get(state, self.timeout_hours)
        
        # Get last activity
        last_activity = self._get_last_activity(conversation)
        if not last_activity:
            return False, "Cannot determine last activity"
        
        # Check timeout
        now = datetime.utcnow()
        time_since_activity = now - last_activity
        
        if time_since_activity >= timedelta(hours=timeout_hours):
            hours_since = int(time_since_activity.total_seconds() / 3600)
            return True, f"No activity for {hours_since} hours (timeout: {timeout_hours}h)"
        
        return False, None


# Global timeout service instance
timeout_service = ConversationTimeoutService()


def check_and_timeout_conversations(limit: int = 100) -> List[str]:
    """Check for timed-out conversations."""
    return timeout_service.check_and_timeout_conversations(limit)


def should_timeout_conversation(conversation_id: str) -> tuple[bool, Optional[str]]:
    """Check if a conversation should be timed out."""
    return timeout_service.should_timeout_conversation(conversation_id)
