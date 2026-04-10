"""
Telnyx webhook signature verification (Ed25519).
Verify telnyx-signature-ed25519 and telnyx-timestamp using TELNYX_PUBLIC_KEY.
"""
import base64
import time
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

TIMESTAMP_TOLERANCE_SECONDS = 300  # 5 minutes (Telnyx doc)


def verify_telnyx_signature(
    raw_body: bytes,
    signature_header: Optional[str],
    timestamp_header: Optional[str],
    public_key_base64: Optional[str],
) -> bool:
    """
    Verify Telnyx webhook signature (Ed25519).
    Signed payload is timestamp + "|" + raw_body (UTF-8).
    Returns True if valid, False if missing/invalid or expired timestamp.
    """
    if not signature_header or not timestamp_header or not public_key_base64:
        return False
    signature_header = signature_header.strip()
    timestamp_header = timestamp_header.strip()
    public_key_base64 = public_key_base64.strip()
    if not signature_header or not timestamp_header or not public_key_base64:
        return False

    try:
        ts = int(timestamp_header)
    except ValueError:
        return False

    now = int(time.time())
    if abs(now - ts) > TIMESTAMP_TOLERANCE_SECONDS:
        return False

    try:
        raw_body.decode("utf-8")
    except UnicodeDecodeError:
        return False

    signed_payload = timestamp_header.encode("utf-8") + b"|" + raw_body

    try:
        signature_bytes = base64.b64decode(signature_header)
        public_key_bytes = base64.b64decode(public_key_base64)
    except Exception:
        return False

    if len(signature_bytes) != 64 or len(public_key_bytes) != 32:
        return False

    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature_bytes, signed_payload)
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False
