"""
In-memory rate limiter for pilot (per-phone). No DynamoDB dependency.
"""
import time
from collections import defaultdict
from threading import Lock

MESSAGES_PER_WINDOW = 10
WINDOW_SECONDS = 60

_timestamps: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def check_rate_limit(phone_number: str) -> tuple[bool, str | None, int | None]:
    """
    Returns (allowed, reason, retry_after_seconds).
    If not allowed, retry_after_seconds is when they can try again.
    """
    now = time.time()
    cutoff = now - WINDOW_SECONDS
    with _lock:
        times = _timestamps[phone_number]
        times[:] = [t for t in times if t > cutoff]
        if len(times) >= MESSAGES_PER_WINDOW:
            oldest = min(times)
            retry_after = int(WINDOW_SECONDS - (now - oldest))
            return False, f"Too many messages. Wait {retry_after} seconds.", max(1, retry_after)
    return True, None, None


def record_message(phone_number: str) -> None:
    with _lock:
        _timestamps[phone_number].append(time.time())
