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
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to E.164 format.
        
        Args:
            phone: Phone number in various formats
            
        Returns:
            Phone number in E.164 format (e.g., +1234567890)
        """
        if not phone:
            return phone
        
        phone = phone.strip()
        # Remove any spaces, dashes, parentheses
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('.', '')
        
        # If it already starts with +, return as is
        if phone.startswith('+'):
            return phone
        
        # Handle US numbers
        if phone.startswith('1') and len(phone) == 11:
            # US number starting with 1 (11 digits total)
            return '+' + phone
        elif len(phone) == 10:
            # US number without country code (10 digits)
            return '+1' + phone
        elif len(phone) == 11 and phone[0] == '1':
            # Already has country code but no +
            return '+' + phone
        else:
            # Assume US and add +1, removing leading 1 if present
            cleaned = phone.lstrip('1')
            if len(cleaned) == 10:
                return '+1' + cleaned
            # If we can't figure it out, just add +1
            return '+1' + phone
    
    def send_sms(
        self,
        to_phone: str,
        message: str,
        from_phone: Optional[str] = None,
        messaging_profile_id: Optional[str] = None
    ) -> Dict:
        """
        Send SMS message via Telnyx.
        
        Args:
            to_phone: Recipient phone number (E.164 format, e.g., +1234567890)
            message: Message text
            from_phone: Sender phone number (defaults to configured number)
            messaging_profile_id: Optional profile ID (e.g. from inbound webhook); if not set, uses env TELNYX_MESSAGING_PROFILE_ID
            
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
        
        # Normalize phone numbers to E.164 format (Telnyx requires + prefix)
        to_phone = self._normalize_phone(to_phone)
        if from_phone:
            from_phone = self._normalize_phone(from_phone)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Telnyx API payload
        # For toll-free numbers, messaging_profile_id is often required
        payload = {
            "to": to_phone,
            "from": from_phone,
            "text": message
        }
        
        # Include messaging profile ID if set (required for toll-free numbers)
        # Prefer argument (e.g. from inbound webhook payload), then env
        profile_id = messaging_profile_id or os.getenv("TELNYX_MESSAGING_PROFILE_ID")
        if profile_id:
            payload["messaging_profile_id"] = profile_id
        
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
        except requests.exceptions.HTTPError as e:
            # Get detailed error message from Telnyx
            error_detail = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    # Telnyx error format: {"errors": [{"detail": "...", "title": "..."}]}
                    if 'errors' in error_data:
                        error_messages = [err.get('detail', err.get('title', str(err))) for err in error_data['errors']]
                        error_detail = "; ".join(error_messages)
                    elif 'detail' in error_data:
                        error_detail = error_data['detail']
                    elif 'message' in error_data:
                        error_detail = error_data['message']
                    else:
                        error_detail = e.response.text
                except:
                    error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            
            print(f"❌ Telnyx API Error: {error_detail}")
            if "Invalid destination number" in error_detail or "Invalid phone number" in error_detail:
                print(f"   💡 Tip: Make sure the recipient phone number is a real, valid phone number")
                print(f"   💡 Test numbers like +15555551234 won't work - use your actual phone number")
            print(f"   Request payload: {payload}")
            return {
                "success": False,
                "error": error_detail,
                "status_code": e.response.status_code if hasattr(e, 'response') and e.response else None
            }
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    if 'errors' in error_data:
                        error_messages = [err.get('detail', err.get('title', str(err))) for err in error_data['errors']]
                        error_detail = "; ".join(error_messages)
                    else:
                        error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
                except:
                    error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            
            print(f"❌ Error sending SMS: {error_detail}")
            return {
                "success": False,
                "error": error_detail
            }

