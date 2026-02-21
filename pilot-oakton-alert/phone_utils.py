"""
Shared phone number normalization (E.164-style for US).
Single source of truth for storage, rate limiting, and SMS send.
"""


def normalize_phone(phone: str) -> str:
    """
    Normalize to E.164-like form for US numbers.
    Empty or invalid input returns "".
    """
    if not phone:
        return ""
    p = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if p.startswith("+"):
        return p
    if len(p) == 10:
        return "+1" + p
    if len(p) == 11 and p.startswith("1"):
        return "+" + p
    return "+1" + p.lstrip("1") if len(p.lstrip("1")) == 10 else p
