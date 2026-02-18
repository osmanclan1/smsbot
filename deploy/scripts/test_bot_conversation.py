#!/usr/bin/env python3
"""
Interactive test script for the SMS bot.
Simulates a conversation without sending actual SMS messages.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from src.api.services.conversation import ConversationEngine
from src.storage.dynamodb import DynamoDBService


def main():
    print("=" * 60)
    print("SMS Bot Test Interface")
    print("=" * 60)
    print("\nThis simulates a conversation with the bot.")
    print("Type 'quit' or 'exit' to end.\n")
    
    engine = ConversationEngine()
    db = DynamoDBService()
    
    # Create test conversation
    test_phone = "+15555551234"
    conversation_id = db.create_conversation(
        phone_number=test_phone,
        trigger_type="default",
        initial_message="Hi! I'm here to help. How can I assist you?"
    )
    
    print("🤖 Bot: Hi! I'm here to help with any questions about Oakton Community College. How can I assist you today?\n")
    
    # Sample questions
    samples = [
        "What are my payment options?",
        "How much does tuition cost?",
        "When does registration open?",
        "How do I apply for financial aid?",
        "What is EZ Pay?",
        "When is the payment deadline?",
        "How do I register for classes?",
        "What happens if I don't pay on time?",
    ]
    
    print("💡 Sample questions you can ask:")
    for i, q in enumerate(samples, 1):
        print(f"   {i}. {q}")
    print()
    
    message_count = 0
    
    while True:
        try:
            user_msg = input("👤 You: ").strip()
            if not user_msg:
                continue
            if user_msg.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            result = engine.process_message(test_phone, user_msg)
            response = result.get('response', '')
            message_count += 1
            
            if response:
                print(f"\n🤖 Bot: {response}\n")
            
            if result.get('action') == 'finish':
                print(f"✅ Conversation completed with action: {result.get('result_type', 'unknown')}\n")
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            import traceback
            traceback.print_exc()
    
    # Show transcript
    if message_count > 0:
        print("=" * 60)
        print("Full Transcript:")
        print("-" * 60)
        conv = db.get_conversation(conversation_id)
        if conv:
            for msg in conv.get('messages', []):
                role = msg.get('role')
                text = msg.get('text')
                if role == 'user':
                    print(f"👤 You: {text}")
                else:
                    print(f"🤖 Bot: {text}")
        print("-" * 60)
        print(f"\n✅ Test complete! Conversation ID: {conversation_id}\n")


if __name__ == "__main__":
    main()
