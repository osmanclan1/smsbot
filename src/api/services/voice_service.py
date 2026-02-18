"""
Voice service for initiating calls via Telnyx Call Control API.
"""

import os
import requests
from typing import Optional, Dict


class VoiceService:
    """Service for initiating voice calls via Telnyx."""
    
    TELNYX_API_URL = "https://api.telnyx.com/v2/calls"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_agent_id: Optional[str] = None,
        phone_number: Optional[str] = None
    ):
        """
        Initialize Voice service.
        
        Args:
            api_key: Telnyx API key (or from env)
            voice_agent_id: Telnyx Voice AI Agent ID (or from env, optional)
            phone_number: Telnyx phone number assigned to Voice AI Agent (or from env)
        """
        self.api_key = api_key or os.getenv("TELNYX_API_KEY")
        self.voice_agent_id = voice_agent_id or os.getenv("TELNYX_VOICE_AGENT_ID")
        self.phone_number = phone_number or os.getenv("TELNYX_PHONE_NUMBER")
        
        # Allow initialization without credentials for testing
        # For voice calls, we need API key and phone number (voice_agent_id is optional)
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
            return '+' + phone
        elif len(phone) == 10:
            return '+1' + phone
        elif len(phone) == 11 and phone[0] == '1':
            return '+' + phone
        else:
            cleaned = phone.lstrip('1')
            if len(cleaned) == 10:
                return '+1' + cleaned
            return '+1' + phone
    
    def initiate_call(
        self,
        to_phone: str,
        from_phone: Optional[str] = None,
        conversation_context: Optional[Dict] = None
    ) -> Dict:
        """
        Initiate a voice call using Telnyx Call Control API.
        
        For Voice AI Agent integration, we initiate an outbound call from the
        phone number assigned to the Voice AI Agent. When the call is answered,
        the Voice AI Agent will automatically handle it and call our webhook.
        
        Args:
            to_phone: Recipient phone number (E.164 format)
            from_phone: Caller phone number (defaults to configured number assigned to agent)
            conversation_context: Optional context to pass to the call
            
        Returns:
            API response dictionary with call_id and status
        """
        # Mock response if Telnyx not configured (for testing)
        if not self.is_configured:
            print("⚠️  Telnyx Voice not configured - returning mock call response")
            return {
                "success": True,
                "data": {"id": "mock-call-id"},
                "call_id": "mock-call-id",
                "mock": True
            }
        
        # Normalize phone numbers
        to_phone = self._normalize_phone(to_phone)
        if not from_phone:
            from_phone = self.phone_number
        if from_phone:
            from_phone = self._normalize_phone(from_phone)
        
        if not from_phone:
            return {
                "success": False,
                "error": "No phone number configured for outbound calls. Set TELNYX_PHONE_NUMBER or pass from_phone parameter."
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Telnyx Call Control API payload
        # We initiate a call from the Voice AI Agent's phone number
        # The agent will automatically answer and handle the call
        payload = {
            "to": to_phone,
            "from": from_phone
        }
        
        # Add conversation context if provided (will be available in webhook)
        if conversation_context:
            # Store context in client_state for webhook access
            import json
            payload["client_state"] = json.dumps({
                "conversation_id": conversation_context.get('conversation_id', ''),
                "trigger_type": conversation_context.get('trigger_type', ''),
                "initial_message": conversation_context.get('initial_message', '')
            })
        
        try:
            response = requests.post(
                self.TELNYX_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            response_data = response.json()
            # Extract call_control_id from response
            # Telnyx returns: {"data": {"call_control_id": "...", ...}}
            call_control_id = None
            if isinstance(response_data, dict):
                data = response_data.get("data", {})
                call_control_id = data.get("call_control_id") or data.get("id")
            
            print(f"✅ Voice call initiated successfully")
            print(f"   To: {to_phone}")
            print(f"   From: {from_phone}")
            print(f"   Call Control ID: {call_control_id}")
            
            return {
                "success": True,
                "data": response_data,
                "call_id": call_control_id
            }
        except requests.exceptions.HTTPError as e:
            error_detail = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
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
            
            print(f"❌ Telnyx Voice API Error: {error_detail}")
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
            
            print(f"❌ Error initiating voice call: {error_detail}")
            return {
                "success": False,
                "error": error_detail
            }

