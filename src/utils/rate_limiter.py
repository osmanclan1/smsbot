"""
Rate limiting service for per-phone-number rate limiting.
"""
import os
import sys
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from threading import Lock
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.dynamodb import DynamoDBService


class RateLimiter:
    """Rate limiter for SMS messages per phone number."""
    
    # Default rate limits
    DEFAULT_MESSAGES_PER_WINDOW = 10  # messages
    DEFAULT_WINDOW_SECONDS = 60  # 1 minute
    
    # Maximum limits (hard cap)
    MAX_MESSAGES_PER_WINDOW = 50
    MAX_WINDOW_SECONDS = 3600  # 1 hour
    
    def __init__(
        self,
        messages_per_window: Optional[int] = None,
        window_seconds: Optional[int] = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            messages_per_window: Number of messages allowed per window (default from env or 10)
            window_seconds: Window size in seconds (default from env or 60)
        """
        self.messages_per_window = int(os.getenv(
            'RATE_LIMIT_MESSAGES_PER_WINDOW',
            messages_per_window or self.DEFAULT_MESSAGES_PER_WINDOW
        ))
        self.window_seconds = int(os.getenv(
            'RATE_LIMIT_WINDOW_SECONDS',
            window_seconds or self.DEFAULT_WINDOW_SECONDS
        ))
        
        # Enforce maximum limits
        self.messages_per_window = min(self.messages_per_window, self.MAX_MESSAGES_PER_WINDOW)
        self.window_seconds = min(self.window_seconds, self.MAX_WINDOW_SECONDS)
        
        self.db = DynamoDBService()
        self._memory_cache: Dict[str, list] = {}  # phone_number -> [timestamps]
        self._memory_lock = Lock()
    
    def check_rate_limit(self, phone_number: str) -> tuple[bool, Optional[str], Optional[int]]:
        """
        Check if phone number is within rate limit.
        
        Args:
            phone_number: Phone number to check
            
        Returns:
            Tuple of (allowed: bool, reason: Optional[str], retry_after: Optional[int])
            If allowed is False, reason explains why and retry_after is seconds until next window
        """
        # Get recent message timestamps for this phone number
        window_start = datetime.utcnow() - timedelta(seconds=self.window_seconds)
        window_start_iso = window_start.isoformat()
        
        recent_messages = self._get_recent_messages(phone_number, window_start_iso)
        
        # Count messages within window
        now = datetime.utcnow()
        window_start_time = now - timedelta(seconds=self.window_seconds)
        
        messages_in_window = [
            msg_time for msg_time in recent_messages
            if msg_time >= window_start_time
        ]
        
        if len(messages_in_window) >= self.messages_per_window:
            # Rate limit exceeded
            oldest_message_in_window = min(messages_in_window)
            seconds_until_oldest_expires = (oldest_message_in_window - window_start_time).total_seconds()
            retry_after = int(self.window_seconds - seconds_until_oldest_expires)
            
            return False, f"Rate limit exceeded: {len(messages_in_window)}/{self.messages_per_window} messages in {self.window_seconds}s window", retry_after
        
        return True, None, None
    
    def record_message(self, phone_number: str):
        """
        Record a message for rate limiting tracking.
        
        Args:
            phone_number: Phone number that sent/received message
        """
        now = datetime.utcnow()
        
        # Store in memory cache (with cleanup)
        with self._memory_lock:
            if phone_number not in self._memory_cache:
                self._memory_cache[phone_number] = []
            
            self._memory_cache[phone_number].append(now)
            
            # Cleanup old entries (keep only last window's worth)
            cutoff = now - timedelta(seconds=self.window_seconds * 2)  # Keep 2x window for safety
            self._memory_cache[phone_number] = [
                msg_time for msg_time in self._memory_cache[phone_number]
                if msg_time >= cutoff
            ]
    
    def _get_recent_messages(self, phone_number: str, since: str) -> list[datetime]:
        """Get recent message timestamps from cache and database."""
        messages = []
        
        # Get from memory cache
        with self._memory_lock:
            cached_timestamps = self._memory_cache.get(phone_number, [])
            for msg_time in cached_timestamps:
                if msg_time.isoformat() >= since:
                    messages.append(msg_time)
        
        # Also check DynamoDB conversations for message timestamps (if table exists)
        # This is a fallback - memory cache is primary
        try:
            conversation = self.db.get_conversation_by_phone(phone_number)
            if conversation:
                conv_messages = conversation.get('messages', [])
                for msg in conv_messages[-20:]:  # Check last 20 messages
                    msg_timestamp_str = msg.get('timestamp')
                    if msg_timestamp_str and msg_timestamp_str >= since:
                        try:
                            msg_time = datetime.fromisoformat(msg_timestamp_str.replace('Z', '+00:00'))
                            if msg_time not in messages:
                                messages.append(msg_time)
                        except:
                            pass
        except Exception as e:
            # Ignore errors - memory cache is primary
            pass
        
        return sorted(messages)


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(phone_number: str) -> tuple[bool, Optional[str], Optional[int]]:
    """Check if phone number is within rate limit."""
    return rate_limiter.check_rate_limit(phone_number)


def record_message(phone_number: str):
    """Record a message for rate limiting."""
    rate_limiter.record_message(phone_number)
