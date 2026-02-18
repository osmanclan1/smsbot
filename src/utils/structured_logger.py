"""
Structured logging utility for observability.
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Optional, Any
import sys
import os as os_module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StructuredLogger:
    """Structured logger for application events."""
    
    def __init__(self, name: str = "smsbot"):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _mask_phone(self, phone: Optional[str]) -> Optional[str]:
        """Mask phone number for privacy (show last 4 digits only)."""
        if not phone:
            return None
        if len(phone) <= 4:
            return "****"
        return "****" + phone[-4:]
    
    def log_event(
        self,
        event_type: str,
        **kwargs
    ):
        """
        Log structured event.
        
        Args:
            event_type: Type of event (e.g., 'message_received', 'trigger_sent')
            **kwargs: Additional event fields
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            **kwargs
        }
        
        # Mask phone numbers
        if 'phone_number' in log_entry:
            log_entry['phone_number'] = self._mask_phone(log_entry['phone_number'])
        if 'from_number' in log_entry:
            log_entry['from_number'] = self._mask_phone(log_entry['from_number'])
        if 'to_number' in log_entry:
            log_entry['to_number'] = self._mask_phone(log_entry['to_number'])
        
        # Output as JSON for log aggregation tools
        self.logger.info(json.dumps(log_entry))
    
    def message_received(
        self,
        phone_number: str,
        message_length: int,
        conversation_id: Optional[str] = None,
        conversation_state: Optional[str] = None
    ):
        """Log message received event."""
        self.log_event(
            'message_received',
            phone_number=phone_number,
            message_length=message_length,
            conversation_id=conversation_id,
            conversation_state=conversation_state
        )
    
    def message_sent(
        self,
        phone_number: str,
        message_id: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log message sent event."""
        self.log_event(
            'message_sent',
            phone_number=phone_number,
            message_id=message_id,
            success=success,
            error=error
        )
    
    def trigger_sent(
        self,
        phone_number: str,
        trigger_type: str,
        trigger_id: str,
        conversation_id: Optional[str] = None,
        suppressed: bool = False,
        reason: Optional[str] = None
    ):
        """Log trigger sent event."""
        self.log_event(
            'trigger_sent' if not suppressed else 'trigger_suppressed',
            phone_number=phone_number,
            trigger_type=trigger_type,
            trigger_id=trigger_id,
            conversation_id=conversation_id,
            suppressed=suppressed,
            reason=reason
        )
    
    def conversation_state_transition(
        self,
        conversation_id: str,
        from_state: str,
        to_state: str,
        active_flow: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """Log conversation state transition."""
        self.log_event(
            'conversation_state_transition',
            conversation_id=conversation_id,
            from_state=from_state,
            to_state=to_state,
            active_flow=active_flow,
            reason=reason
        )
    
    def conversation_finished(
        self,
        conversation_id: str,
        result_type: str,
        phone_number: str,
        message_count: int,
        duration_seconds: Optional[float] = None
    ):
        """Log conversation finished event."""
        self.log_event(
            'conversation_finished',
            conversation_id=conversation_id,
            result_type=result_type,
            phone_number=phone_number,
            message_count=message_count,
            duration_seconds=duration_seconds
        )
    
    def escalation(
        self,
        conversation_id: str,
        phone_number: str,
        escalation_reason: str,
        trigger_type: Optional[str] = None
    ):
        """Log escalation event."""
        self.log_event(
            'escalation',
            conversation_id=conversation_id,
            phone_number=phone_number,
            escalation_reason=escalation_reason,
            trigger_type=trigger_type
        )
    
    def opt_out(
        self,
        phone_number: str,
        action: str  # 'opt_out' or 'opt_in'
    ):
        """Log opt-out/opt-in event."""
        self.log_event(
            'opt_out' if action == 'opt_out' else 'opt_in',
            phone_number=phone_number
        )


# Global logger instance
logger = StructuredLogger()


# Convenience functions
def log_message_received(phone_number: str, message_length: int, conversation_id: Optional[str] = None, conversation_state: Optional[str] = None):
    """Log message received."""
    logger.message_received(phone_number, message_length, conversation_id, conversation_state)


def log_message_sent(phone_number: str, message_id: Optional[str] = None, success: bool = True, error: Optional[str] = None):
    """Log message sent."""
    logger.message_sent(phone_number, message_id, success, error)


def log_trigger_sent(phone_number: str, trigger_type: str, trigger_id: str, conversation_id: Optional[str] = None, suppressed: bool = False, reason: Optional[str] = None):
    """Log trigger sent."""
    logger.trigger_sent(phone_number, trigger_type, trigger_id, conversation_id, suppressed, reason)


def log_state_transition(conversation_id: str, from_state: str, to_state: str, active_flow: Optional[str] = None, reason: Optional[str] = None):
    """Log state transition."""
    logger.conversation_state_transition(conversation_id, from_state, to_state, active_flow, reason)


def log_conversation_finished(conversation_id: str, result_type: str, phone_number: str, message_count: int, duration_seconds: Optional[float] = None):
    """Log conversation finished."""
    logger.conversation_finished(conversation_id, result_type, phone_number, message_count, duration_seconds)


def log_escalation(conversation_id: str, phone_number: str, escalation_reason: str, trigger_type: Optional[str] = None):
    """Log escalation."""
    logger.escalation(conversation_id, phone_number, escalation_reason, trigger_type)


def log_opt_out(phone_number: str, action: str):
    """Log opt-out/opt-in."""
    logger.opt_out(phone_number, action)
