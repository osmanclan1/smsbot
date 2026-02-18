"""
Test script for voice integration flow.
Tests voice webhook, conversation creation, and channel switching.
"""

import requests
import json
import os
from typing import Dict, Optional

# Configuration
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
VOICE_WEBHOOK_URL = f"{API_BASE}/api/voice/webhook"
TEST_PHONE = os.getenv("TEST_PHONE", "+16699003917")


def test_voice_webhook(transcript: str, phone_number: str = TEST_PHONE) -> Dict:
    """
    Test voice webhook endpoint.
    
    Args:
        transcript: Transcribed user speech
        phone_number: Caller's phone number
        
    Returns:
        Response from webhook
    """
    print(f"\n📞 Testing voice webhook...")
    print(f"   Transcript: {transcript}")
    print(f"   Phone: {phone_number}")
    
    payload = {
        "transcript": transcript,
        "caller_id": phone_number,
        "call_id": f"test-call-{hash(transcript) % 10000}"
    }
    
    try:
        response = requests.post(
            VOICE_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"   ✅ Response received:")
        print(f"      Conversation ID: {data.get('conversation_id', 'N/A')}")
        print(f"      Response: {data.get('response', '')[:100]}...")
        return data
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"      Status: {e.response.status_code}")
            print(f"      Body: {e.response.text}")
        return {"error": str(e)}


def test_sms_after_voice(phone_number: str = TEST_PHONE, message: str = "Can you send me the payment link?") -> Dict:
    """
    Test sending SMS after a voice conversation to verify conversation sharing.
    
    Args:
        phone_number: Phone number
        message: SMS message
        
    Returns:
        Response from SMS webhook
    """
    print(f"\n💬 Testing SMS after voice (channel switching)...")
    print(f"   Message: {message}")
    print(f"   Phone: {phone_number}")
    
    # Simulate SMS webhook payload
    payload = {
        "data": {
            "event_type": "message.received",
            "payload": {
                "from": {"phone_number": phone_number},
                "to": [{"phone_number": "+18334209112"}],
                "text": message
            }
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/sms/webhook",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"   ✅ SMS processed successfully")
        return data
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"      Status: {e.response.status_code}")
            print(f"      Body: {e.response.text}")
        return {"error": str(e)}


def test_voice_conversation_flow():
    """
    Test a complete voice conversation flow.
    """
    print("\n" + "="*60)
    print("VOICE CONVERSATION FLOW TEST")
    print("="*60)
    
    phone = TEST_PHONE
    
    # Step 1: Initial voice call
    print("\n1️⃣  Initial Voice Call")
    result1 = test_voice_webhook(
        "Hi, I need help with my payment deadline",
        phone
    )
    conv_id = result1.get('conversation_id')
    
    if not conv_id:
        print("   ⚠️  No conversation ID returned, cannot continue test")
        return
    
    # Step 2: Follow-up voice message
    print("\n2️⃣  Follow-up Voice Message")
    result2 = test_voice_webhook(
        "How much do I owe?",
        phone
    )
    
    # Step 3: Switch to SMS
    print("\n3️⃣  Switching to SMS Channel")
    result3 = test_sms_after_voice(
        phone,
        "Can you send me the payment link via text?"
    )
    
    # Step 4: Back to voice
    print("\n4️⃣  Back to Voice Channel")
    result4 = test_voice_webhook(
        "Thanks, I'll check the link",
        phone
    )
    
    print("\n" + "="*60)
    print("✅ Voice conversation flow test completed!")
    print("="*60)
    print(f"\nConversation ID: {conv_id}")
    print("   - Should be shared across all voice and SMS messages")


def test_voice_webhook_formats():
    """
    Test different webhook payload formats that Telnyx might send.
    """
    print("\n" + "="*60)
    print("VOICE WEBHOOK FORMAT TESTING")
    print("="*60)
    
    phone = TEST_PHONE
    
    # Format 1: Direct format
    print("\n📋 Testing Format 1: Direct format")
    payload1 = {
        "transcript": "Hello, I need help",
        "caller_id": phone,
        "call_id": "call-123"
    }
    test_webhook_payload(payload1)
    
    # Format 2: Nested format
    print("\n📋 Testing Format 2: Nested format")
    payload2 = {
        "data": {
            "transcript": "What's my balance?",
            "caller": {"phone_number": phone},
            "call_id": "call-456"
        }
    }
    test_webhook_payload(payload2)
    
    # Format 3: Webhook tool format
    print("\n📋 Testing Format 3: Webhook tool format")
    payload3 = {
        "user_message": "I want to register for classes",
        "phone_number": phone,
        "call_id": "call-789"
    }
    test_webhook_payload(payload3)
    
    # Format 4: Alternative field names
    print("\n📋 Testing Format 4: Alternative field names")
    payload4 = {
        "message": "When is the payment deadline?",
        "from": phone,
        "call_id": "call-101"
    }
    test_webhook_payload(payload4)


def test_webhook_payload(payload: Dict):
    """
    Test a specific webhook payload format.
    
    Args:
        payload: Webhook payload to test
    """
    try:
        response = requests.post(
            VOICE_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"   ✅ Format accepted")
        print(f"      Response: {data.get('response', '')[:80]}...")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"      Status: {e.response.status_code}")
            print(f"      Body: {e.response.text[:200]}")


def test_voice_health():
    """
    Test voice service health endpoint.
    """
    print("\n" + "="*60)
    print("VOICE HEALTH CHECK")
    print("="*60)
    
    try:
        response = requests.get(
            f"{API_BASE}/api/voice/health",
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Voice service is healthy")
        print(f"   Status: {data.get('status')}")
        print(f"   Service: {data.get('service')}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("VOICE INTEGRATION TEST SUITE")
    print("="*60)
    print(f"\nAPI Base: {API_BASE}")
    print(f"Test Phone: {TEST_PHONE}")
    
    # Run tests
    test_voice_health()
    test_voice_webhook_formats()
    test_voice_conversation_flow()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
    print("\nNext steps:")
    print("1. Configure Telnyx Voice AI Agent with webhook URL")
    print("2. Test actual voice call from phone")
    print("3. Verify conversation history is shared between SMS and voice")
    print("4. Test outbound voice triggers via admin dashboard")


