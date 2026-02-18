#!/usr/bin/env python3
"""
Quick SMS test - just provide phone number and message as arguments.
Usage: python quick_test_sms.py +1234567890 "Your message here"
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from dotenv import load_dotenv
load_dotenv()

from src.api.services.sms_service import SMSService

def main():
    if len(sys.argv) < 3:
        print("Usage: python quick_test_sms.py <to_phone> <message>")
        print("Example: python quick_test_sms.py +1234567890 'Hello, this is a test!'")
        sys.exit(1)
    
    to_phone = sys.argv[1]
    message = sys.argv[2]
    
    api_key = os.getenv("TELNYX_API_KEY")
    from_phone = os.getenv("TELNYX_PHONE_NUMBER")
    
    if not api_key:
        print("❌ TELNYX_API_KEY not set in environment")
        print("   Set it: export TELNYX_API_KEY=your_key")
        sys.exit(1)
    
    if not from_phone:
        print("❌ TELNYX_PHONE_NUMBER not set in environment")
        print("   Set it: export TELNYX_PHONE_NUMBER=+1234567890")
        sys.exit(1)
    
    print(f"📤 Sending SMS...")
    print(f"   From: {from_phone}")
    print(f"   To: {to_phone}")
    print(f"   Message: {message}")
    
    sms_service = SMSService(api_key=api_key, phone_number=from_phone)
    result = sms_service.send_sms(to_phone, message)
    
    if result.get('success'):
        print("✅ SMS sent successfully!")
        if result.get('message_id'):
            print(f"   Message ID: {result.get('message_id')}")
        return 0
    else:
        print("❌ Failed to send SMS")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())


