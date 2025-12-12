#!/usr/bin/env python3
"""
Test script for easy win features.
Tests all 6 features and reports results.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from dotenv import load_dotenv
load_dotenv()

from src.api.services.conversation import ConversationEngine

def test_feature(engine, feature_name, test_message, phone_number="+15555551234"):
    """Test a single feature."""
    print(f"\n{'='*60}")
    print(f"Testing: {feature_name}")
    print(f"Input: {test_message}")
    print(f"{'='*60}")
    
    try:
        result = engine.process_message(phone_number, test_message)
        response = result.get('response', 'No response')
        
        if 'error' in response.lower() and 'sorry' in response.lower():
            print(f"❌ ERROR: {response}")
            return False
        else:
            print(f"✅ Response ({len(response)} chars):")
            print(f"   {response[:200]}..." if len(response) > 200 else f"   {response}")
            return True
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("EASY WIN FEATURES TEST")
    print("="*60)
    
    engine = ConversationEngine()
    test_phone = "+15555559999"  # Use different number to avoid conflicts
    
    results = {}
    
    # Test 1: Link Mode
    results['Link Mode'] = test_feature(
        engine, 
        "1. Send Me the Right Link Mode",
        "where do I pay",
        test_phone
    )
    
    # Test 2: Policy Explainer
    results['Policy Explainer'] = test_feature(
        engine,
        "2. Explain Policies (Plain English)",
        "explain the withdrawal policy",
        test_phone
    )
    
    # Test 3: Financial Aid Explainer
    results['Financial Aid'] = test_feature(
        engine,
        "3. Financial Aid Explainer",
        "what is FAFSA",
        test_phone
    )
    
    # Test 4: Hold Diagnosis (first message)
    results['Hold Diagnosis'] = test_feature(
        engine,
        "4. Hold Diagnosis + Fix Guide",
        "I have a hold",
        test_phone
    )
    
    # Test 5: Registration Troubleshooter (first message)
    results['Registration Troubleshooter'] = test_feature(
        engine,
        "5. Registration Troubleshooter",
        "why can't I register",
        test_phone
    )
    
    # Test 6: Next Steps Wizard (first message)
    results['Next Steps Wizard'] = test_feature(
        engine,
        "6. Next Steps Wizard",
        "what do I need to do next",
        test_phone
    )
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} features working")
    print("\nDetailed Results:")
    for feature, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {feature}: {status}")
    
    print("\n" + "="*60)
    if passed == total:
        print("🎉 ALL FEATURES WORKING!")
    else:
        print(f"⚠️  {total - passed} feature(s) need attention")
    print("="*60)

if __name__ == "__main__":
    main()

