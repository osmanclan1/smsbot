#!/usr/bin/env python3
"""
Comprehensive test script for all new features.
Tests each feature and reports results.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from dotenv import load_dotenv
load_dotenv()

from src.api.services.conversation import ConversationEngine

def test_feature(engine, feature_name, test_message, expected_keywords=None):
    """Test a single feature and return results."""
    print(f"\n{'='*60}")
    print(f"Testing: {feature_name}")
    print(f"Input: {test_message}")
    print(f"{'='*60}")
    
    try:
        test_phone = "+15555551234"
        result = engine.process_message(test_phone, test_message)
        response = result.get('response', 'No response')
        
        # Check if response contains expected keywords
        passed = True
        if expected_keywords:
            response_lower = response.lower()
            missing = [kw for kw in expected_keywords if kw.lower() not in response_lower]
            if missing:
                passed = False
                print(f"⚠️  Missing keywords: {missing}")
        
        print(f"Response ({len(response)} chars):")
        print(f"  {response[:300]}..." if len(response) > 300 else f"  {response}")
        
        if passed:
            print(f"✅ PASSED")
        else:
            print(f"⚠️  PARTIAL (missing some keywords)")
        
        return {
            'feature': feature_name,
            'input': test_message,
            'response': response,
            'passed': passed,
            'length': len(response)
        }
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'feature': feature_name,
            'input': test_message,
            'error': str(e),
            'passed': False
        }

def main():
    print("="*60)
    print("COMPREHENSIVE FEATURE TEST")
    print("="*60)
    print("\nTesting all 6 new features...")
    
    engine = ConversationEngine()
    results = []
    
    # Test 1: Link Mode
    results.append(test_feature(
        engine,
        "1. Send Me the Right Link Mode",
        "where do I pay",
        expected_keywords=['http', 'payment', 'link']
    ))
    
    # Test 2: Policy Explainer
    results.append(test_feature(
        engine,
        "2. Explain Policies (Plain English)",
        "explain the withdrawal policy",
        expected_keywords=['withdrawal', 'policy']
    ))
    
    # Test 3: Financial Aid Explainer
    results.append(test_feature(
        engine,
        "3. Financial Aid Explainer",
        "why didn't my aid hit",
        expected_keywords=['aid', 'financial', 'delay']
    ))
    
    # Test 4: Hold Diagnosis
    results.append(test_feature(
        engine,
        "4. Hold Diagnosis + Fix Guide",
        "I have a hold",
        expected_keywords=['hold', 'message']
    ))
    
    # Test 5: Registration Troubleshooter
    results.append(test_feature(
        engine,
        "5. Registration Troubleshooter",
        "why can't I register",
        expected_keywords=['register', 'error', 'message']
    ))
    
    # Test 6: Next Steps Wizard
    results.append(test_feature(
        engine,
        "6. Next Steps Wizard",
        "what do I need to do next",
        expected_keywords=['next', 'step', 'checklist']
    ))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r.get('passed', False))
    total = len(results)
    
    print(f"\nResults: {passed}/{total} features passed")
    print("\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result.get('passed', False) else "❌ FAIL"
        feature = result.get('feature', 'Unknown')
        if 'error' in result:
            print(f"  {i}. {feature}: ❌ ERROR - {result['error']}")
        else:
            length = result.get('length', 0)
            print(f"  {i}. {feature}: {status} ({length} chars)")
    
    print("\n" + "="*60)
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {total - passed} test(s) need attention")
    print("="*60)

if __name__ == "__main__":
    main()

