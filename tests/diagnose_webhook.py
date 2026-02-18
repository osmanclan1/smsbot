#!/usr/bin/env python3
"""
Diagnostic script to check webhook configuration and test webhook endpoint.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

import requests
from dotenv import load_dotenv

load_dotenv()

def diagnose_webhook():
    """Diagnose webhook issues."""
    print("=" * 60)
    print("Webhook Diagnostic")
    print("=" * 60)
    
    # Check if server is running
    print("\n1. Checking if server is running...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running on http://localhost:8000")
        else:
            print(f"   ⚠️  Server responded with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Server is NOT running on http://localhost:8000")
        print("   💡 Start server with: uvicorn src.api.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test webhook endpoint
    print("\n2. Testing webhook endpoint...")
    test_payload = {
        "data": {
            "event_type": "message.received",
            "payload": {
                "from": {"phone_number": "+16699003917"},
                "to": [{"phone_number": "+18334209112"}],
                "text": "Test webhook message"
            }
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/sms/webhook",
            json=test_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Webhook endpoint is working!")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Webhook endpoint returned status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error testing webhook: {e}")
        return False
    
    # Check Telnyx configuration
    print("\n3. Checking Telnyx configuration...")
    api_key = os.getenv("TELNYX_API_KEY")
    phone_number = os.getenv("TELNYX_PHONE_NUMBER")
    messaging_profile_id = os.getenv("TELNYX_MESSAGING_PROFILE_ID")
    
    print(f"   API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"   Phone Number: {phone_number if phone_number else '❌ Missing'}")
    print(f"   Messaging Profile ID: {messaging_profile_id if messaging_profile_id else '⚠️  Not set'}")
    
    # Webhook configuration instructions
    print("\n" + "=" * 60)
    print("Webhook Configuration")
    print("=" * 60)
    print("\n⚠️  IMPORTANT: For SMS to work, you need to configure the webhook in Telnyx!")
    print("\nFor LOCAL DEVELOPMENT:")
    print("1. Install ngrok: brew install ngrok")
    print("2. Start your server: uvicorn src.api.main:app --reload --port 8000")
    print("3. In another terminal, run: ngrok http 8000")
    print("4. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)")
    print("5. Go to Telnyx dashboard → Your phone number → Messaging settings")
    print("6. Set webhook URL to: https://your-ngrok-url.ngrok.io/api/sms/webhook")
    print("\nFor PRODUCTION:")
    print("1. Deploy your API (AWS Lambda, etc.)")
    print("2. Get your API Gateway URL")
    print("3. Set webhook URL to: https://your-api-url/api/sms/webhook")
    print("\n" + "=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        diagnose_webhook()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


