"""
SMS service for sending messages via Telnyx API.
"""

import os
import requests
from typing import Optional, Dict


class SMSService:
    """Service for sending SMS via Telnyx."""
    
    TELNYX_API_URL = "https://api.telnyx.com/v2/messages"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        phone_number: Optional[str] = None
    ):
        """
        Initialize SMS service.
        
        Args:
            api_key: Telnyx API key (or from env)
            phone_number: Telnyx phone number (or from env)
        """
        self.api_key = api_key or os.getenv("TELNYX_API_KEY")
        self.phone_number = phone_number or os.getenv("TELNYX_PHONE_NUMBER")
        
        # Allow initialization without credentials for testing (will return mock responses)
        self.is_configured = bool(self.api_key and self.phone_number)
    
    def send_sms(
        self,
        to_phone: str,
        message: str,
        from_phone: Optional[str] = None
    ) -> Dict:
        """
        Send SMS message via Telnyx.
        
        Args:
            to_phone: Recipient phone number (E.164 format, e.g., +1234567890)
            message: Message text
            from_phone: Sender phone number (defaults to configured number)
            
        Returns:
            API response dictionary
        """
        # Mock response if Telnyx not configured (for testing)
        if not self.is_configured:
            print("⚠️  Telnyx not configured - returning mock SMS response")
            return {
                "success": True,
                "data": {"id": "mock-message-id"},
                "message_id": "mock-message-id",
                "mock": True
            }
        
        if not from_phone:
            from_phone = self.phone_number
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "to": to_phone,
            "from": from_phone,
            "text": message
        }
        
        try:
            response = requests.post(
                self.TELNYX_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json(),
                "message_id": response.json().get("data", {}).get("id")
            }
        except requests.exceptions.RequestException as e:
            print(f"Error sending SMS: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text if hasattr(e.response, 'text') else 'No response text'}")
            return {
                "success": False,
                "error": str(e)
            }

