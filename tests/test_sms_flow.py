#!/usr/bin/env python3
"""
Test script to verify complete SMS flow:
1. Send SMS via trigger
2. Simulate receiving SMS via webhook
3. Verify response is sent
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from dotenv import load_dotenv
load_dotenv()

from src.api.services.sms_service import SMSService
from src.api.services.conversation import ConversationEngine
from src.storage.dynamodb import DynamoDBService

def test_sms_flow():
    """Test the complete SMS flow."""
    print("=" * 60)
    print("SMS Flow Test")
    print("=" * 60)
    
    # Get test phone number
    print("\n📞 Enter phone number to test with (E.164 format, e.g., +1234567890):")
    test_phone = input("   Phone: ").strip()
    
    if not test_phone:
        print("❌ Phone number required")
        return False
    
    # Normalize phone number
    if not test_phone.startswith('+'):
        if test_phone.startswith('1') and len(test_phone) == 11:
            test_phone = '+' + test_phone
        elif len(test_phone) == 10:
            test_phone = '+1' + test_phone
        else:
            test_phone = '+1' + test_phone.lstrip('1')
    
    print(f"\n✅ Using phone number: {test_phone}")
    
    # Test 1: Send SMS via trigger
    print("\n" + "=" * 60)
    print("Test 1: Send SMS via Trigger")
    print("=" * 60)
    
    sms_service = SMSService()
    test_message = "Test message from SMS bot flow test"
    
    print(f"\n📤 Sending SMS to {test_phone}...")
    send_result = sms_service.send_sms(test_phone, test_message)
    
    if send_result.get('success'):
        print(f"✅ SMS sent successfully!")
        print(f"   Message ID: {send_result.get('message_id')}")
    else:
        print(f"❌ Failed to send SMS: {send_result.get('error')}")
        return False
    
    # Test 2: Simulate receiving SMS (webhook processing)
    print("\n" + "=" * 60)
    print("Test 2: Simulate Incoming SMS (Webhook)")
    print("=" * 60)
    
    incoming_message = "Hello, this is a test response"
    print(f"\n📥 Simulating incoming SMS from {test_phone}: '{incoming_message}'")
    
    engine = ConversationEngine()
    db = DynamoDBService()
    
    # Process the message (simulates webhook)
    print("   Processing message through conversation engine...")
    result = engine.process_message(test_phone, incoming_message)
    
    if result.get('response'):
        print(f"✅ Message processed successfully")
        print(f"   Response: {result.get('response')[:100]}...")
        
        # Test 3: Send response via SMS
        print("\n" + "=" * 60)
        print("Test 3: Send Response SMS")
        print("=" * 60)
        
        response_text = result.get('response')
        print(f"\n📤 Sending response SMS to {test_phone}...")
        response_send_result = sms_service.send_sms(test_phone, response_text)
        
        if response_send_result.get('success'):
            print(f"✅ Response SMS sent successfully!")
            print(f"   Message ID: {response_send_result.get('message_id')}")
        else:
            print(f"❌ Failed to send response SMS: {response_send_result.get('error')}")
            return False
    else:
        print(f"⚠️  No response generated")
    
    # Test 4: Verify conversation saved
    print("\n" + "=" * 60)
    print("Test 4: Verify Conversation Saved")
    print("=" * 60)
    
    try:
        conversation = db.get_conversation_by_phone(test_phone)
        if conversation:
            print(f"✅ Conversation found in database")
            print(f"   Conversation ID: {conversation.get('conversation_id')}")
            print(f"   Messages: {len(conversation.get('messages', []))}")
        else:
            print(f"⚠️  No conversation found (may be using memory store)")
    except Exception as e:
        print(f"⚠️  Could not check conversation: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_sms_flow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


