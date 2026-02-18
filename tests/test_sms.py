#!/usr/bin/env python3
"""
Test script for sending SMS via Telnyx.
Tests the toll-free verified number.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from dotenv import load_dotenv
load_dotenv()

from src.api.services.sms_service import SMSService

def test_sms():
    """Test sending an SMS message."""
    print("=" * 60)
    print("SMS Test - Toll-Free Number")
    print("=" * 60)
    
    # Get configuration
    api_key = os.getenv("TELNYX_API_KEY")
    phone_number = os.getenv("TELNYX_PHONE_NUMBER")
    
    print(f"\n📱 Configuration:")
    print(f"   API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"   Phone Number: {phone_number if phone_number else '❌ Missing'}")
    
    if not api_key or not phone_number:
        print("\n❌ Missing configuration!")
        print("\nPlease set in .env file:")
        print("   TELNYX_API_KEY=your_api_key")
        print("   TELNYX_PHONE_NUMBER=+1234567890")
        print("\nOr export as environment variables:")
        print("   export TELNYX_API_KEY=your_api_key")
        print("   export TELNYX_PHONE_NUMBER=+1234567890")
        return False
    
    # Initialize SMS service
    sms_service = SMSService(api_key=api_key, phone_number=phone_number)
    
    # Get test phone number
    print(f"\n📞 Enter recipient phone number (E.164 format, e.g., +1234567890):")
    to_phone = input("   To: ").strip()
    
    if not to_phone:
        print("❌ Phone number required")
        return False
    
    # Ensure E.164 format
    if not to_phone.startswith('+'):
        print("⚠️  Warning: Phone number should start with + (E.164 format)")
        use_anyway = input("   Continue anyway? (y/n): ").strip().lower()
        if use_anyway != 'y':
            return False
    
    # Get test message
    print(f"\n💬 Enter test message (or press Enter for default):")
    message = input("   Message: ").strip()
    
    if not message:
        message = f"Test message from {phone_number}. This is a test of the SMS bot system."
        print(f"   Using default: {message}")
    
    # Confirm
    print(f"\n📤 Ready to send:")
    print(f"   From: {phone_number}")
    print(f"   To: {to_phone}")
    print(f"   Message: {message}")
    
    confirm = input("\n   Send? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return False
    
    # Send SMS
    print(f"\n🚀 Sending SMS...")
    result = sms_service.send_sms(to_phone, message)
    
    # Check result
    if result.get('success'):
        print("✅ SMS sent successfully!")
        if result.get('message_id'):
            print(f"   Message ID: {result.get('message_id')}")
        if result.get('mock'):
            print("   ⚠️  Note: This was a mock response (Telnyx not fully configured)")
        return True
    else:
        print("❌ Failed to send SMS")
        error = result.get('error', 'Unknown error')
        print(f"   Error: {error}")
        return False

if __name__ == "__main__":
    try:
        success = test_sms()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


