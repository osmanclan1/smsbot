#!/usr/bin/env python3
"""
Diagnostic script for Telnyx SMS issues.
Checks configuration and tests API connection.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from dotenv import load_dotenv
load_dotenv()

import requests

def diagnose():
    """Diagnose Telnyx configuration and API issues."""
    print("=" * 60)
    print("Telnyx SMS Diagnostic")
    print("=" * 60)
    
    # Check environment variables
    api_key = os.getenv("TELNYX_API_KEY")
    phone_number = os.getenv("TELNYX_PHONE_NUMBER")
    messaging_profile_id = os.getenv("TELNYX_MESSAGING_PROFILE_ID")
    
    print(f"\n📋 Configuration:")
    print(f"   API Key: {'✅ Set' if api_key else '❌ Missing'}")
    if api_key:
        print(f"   API Key (first 10 chars): {api_key[:10]}...")
    print(f"   Phone Number: {phone_number if phone_number else '❌ Missing'}")
    print(f"   Messaging Profile ID: {messaging_profile_id if messaging_profile_id else '⚠️  Not set (may be required for toll-free)'}")
    
    if not api_key or not phone_number:
        print("\n❌ Missing required configuration!")
        return False
    
    # Test API connection - get phone number info
    print(f"\n🔍 Testing API connection...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try to get phone number details
    try:
        # Get messaging profiles (to check if we need one)
        print("   Checking messaging profiles...")
        profiles_response = requests.get(
            "https://api.telnyx.com/v2/messaging_profiles",
            headers=headers,
            timeout=10
        )
        
        if profiles_response.status_code == 200:
            profiles = profiles_response.json().get('data', [])
            print(f"   ✅ Found {len(profiles)} messaging profile(s)")
            if profiles:
                print(f"   Profile IDs:")
                for profile in profiles[:3]:  # Show first 3
                    print(f"      - {profile.get('id')} ({profile.get('name', 'Unnamed')})")
                if not messaging_profile_id and profiles:
                    print(f"   💡 Tip: You may need to set TELNYX_MESSAGING_PROFILE_ID")
        else:
            print(f"   ⚠️  Could not fetch profiles: {profiles_response.status_code}")
        
        # Try to get phone number details
        print(f"\n   Checking phone number: {phone_number}...")
        # URL encode the phone number
        import urllib.parse
        encoded_phone = urllib.parse.quote(phone_number)
        phone_response = requests.get(
            f"https://api.telnyx.com/v2/phone_numbers/{encoded_phone}",
            headers=headers,
            timeout=10
        )
        
        if phone_response.status_code == 200:
            phone_data = phone_response.json().get('data', {})
            print(f"   ✅ Phone number found")
            print(f"      Number: {phone_data.get('phone_number')}")
            print(f"      Type: {phone_data.get('number_type', 'Unknown')}")
            print(f"      Messaging Profile: {phone_data.get('messaging_profile_id', 'None')}")
            
            if not phone_data.get('messaging_profile_id'):
                print(f"   ⚠️  WARNING: Phone number has no messaging profile!")
                print(f"   💡 You may need to assign a messaging profile in Telnyx dashboard")
        elif phone_response.status_code == 404:
            print(f"   ❌ Phone number not found in your account")
        else:
            print(f"   ⚠️  Status {phone_response.status_code}: {phone_response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test sending a message (dry run - show what would be sent)
    print(f"\n📤 Test Message Payload:")
    test_to = "+15555551234"  # Example
    payload = {
        "to": test_to,
        "from": phone_number,
        "text": "Test message"
    }
    if messaging_profile_id:
        payload["messaging_profile_id"] = messaging_profile_id
    
    print(f"   {payload}")
    
    print(f"\n💡 Common Issues:")
    print(f"   1. Toll-free numbers often require a messaging_profile_id")
    print(f"   2. Phone number must be verified in Telnyx dashboard")
    print(f"   3. API key must have 'messaging' permissions")
    print(f"   4. Phone numbers must be in E.164 format (+1XXXXXXXXXX)")
    
    return True

if __name__ == "__main__":
    try:
        diagnose()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


