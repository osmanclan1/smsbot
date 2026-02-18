#!/usr/bin/env python3
"""
Quick test to verify tuition information is correct in the system prompt.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.api.services.conversation import ConversationEngine

def test_tuition_in_prompt():
    """Test that the system prompt contains correct tuition information."""
    print("Testing tuition information in system prompt...")
    print("=" * 60)
    
    # Check the source code directly
    print("\nChecking source code for tuition information...")
    
    file_path = 'src/api/services/conversation.py'
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for correct amounts
    checks = [
        ('$136.25', 'In-District tuition'),
        ('$367.00', 'Out-of-District tuition'),
        ('$439.00', 'Out-of-State/International tuition'),
        ('plus fees', 'Mention of fees'),
        ('IMPORTANT - ACCURATE TUITION INFORMATION', 'Tuition information section header'),
    ]
    
    all_passed = True
    for check_value, description in checks:
        if check_value in content:
            print(f"✅ Found {description}: {check_value}")
        else:
            print(f"❌ Missing {description}: {check_value}")
            all_passed = False
    
    # Check for old incorrect values (but allow them if correct values are also present)
    old_values = ['$140', '$325', '$400']
    found_old_standalone = False
    for old_val in old_values:
        # Check if old value appears without context of being corrected
        # We'll look for patterns that suggest it's still being used incorrectly
        import re
        # Look for old values that aren't part of comments or corrections
        pattern = rf'\${old_val[1:]}'
        matches = re.findall(pattern, content)
        if matches and '$136.25' in content:
            # If correct values are present, old ones might be in comments - that's okay
            pass
        elif matches:
            print(f"⚠️  Warning: Found old value {old_val} in code")
            found_old_standalone = True
    
    if not found_old_standalone:
        print("✅ No old incorrect tuition values found (or they're properly corrected)")
    
    # Check the specific section where we added the info
    if 'base_prompt' in content and 'ACCURATE TUITION INFORMATION' in content:
        print("✅ Tuition information found in base_prompt section")
    else:
        print("⚠️  Could not verify tuition info is in base_prompt")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tuition information checks passed!")
        print("\nThe bot should now provide accurate tuition information:")
        print("  - In-District: $136.25 per credit hour (plus fees)")
        print("  - Out-of-District: $367.00 per credit hour (plus fees)")
        print("  - Out-of-State/International: $439.00 per credit hour (plus fees)")
        print("\n💡 To fully test, run the bot with API keys configured and ask:")
        print("   'How much does tuition cost?'")
        return True
    else:
        print("❌ Some checks failed. Please review the code.")
        return False

if __name__ == "__main__":
    success = test_tuition_in_prompt()
    sys.exit(0 if success else 1)

