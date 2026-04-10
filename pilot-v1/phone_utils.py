"""
Shared phone number normalization (E.164-style for US).
Single source of truth for storage, rate limiting, and SMS send.
"""

import re


_E164_RE = re.compile(r"^\+[1-9]\d{9,14}$")


def is_valid_e164(phone: str) -> bool:
    return bool(phone and _E164_RE.fullmatch(phone))


def normalize_phone(phone: str) -> str:
    """
    Normalize to E.164-like form for US numbers.
    Empty or invalid input returns "".
    """
    if not phone:
        return ""
    p = (
        phone.strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )
    # Common copy/paste artifact for extensions.
    p = re.sub(r"(ext|x)\d+$", "", p, flags=re.IGNORECASE)

    if p.startswith("+"):
        return p if is_valid_e164(p) else ""
    if len(p) == 10:
        return "+1" + p
    if len(p) == 11 and p.startswith("1"):
        return "+" + p
    trimmed = p.lstrip("1")
    if len(trimmed) == 10 and trimmed.isdigit():
        return "+1" + trimmed
    return ""
