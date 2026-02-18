#!/usr/bin/env python3
"""Direct Telnyx API test to see actual error message."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TELNYX_API_KEY")
from_phone = os.getenv("TELNYX_PHONE_NUMBER")
to_phone = "+15555551234"  # Test number
messaging_profile_id = os.getenv("TELNYX_MESSAGING_PROFILE_ID")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "to": to_phone,
    "from": from_phone,
    "text": "Test message"
}

if messaging_profile_id:
    payload["messaging_profile_id"] = messaging_profile_id

print("Sending request to Telnyx...")
print(f"Payload: {payload}")

response = requests.post(
    "https://api.telnyx.com/v2/messages",
    headers=headers,
    json=payload,
    timeout=10
)

print(f"\nStatus Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")
print(f"\nResponse Body:")
try:
    print(response.json())
except:
    print(response.text)


