"""
Oakton Alert pilot – intent matching and canned responses.
No OpenAI; keyword/phrase patterns only. Returns canned response or 'other'.
"""
import re
from typing import Tuple, Optional

import messages
import config


def _normalize(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.lower().strip().split())


# Intent: (list of regex pattern strings), response (built with config at import time)
_INTENT_SPECS = [
    (
        "where_how_pay",
        [
            r"\bwhere\s+(do\s+i\s+)?(pay|go\s+to\s+pay)",
            r"\bhow\s+do\s+i\s+pay",
            r"\bpayment\s+link",
            r"\bpay\s+my\s+balance",
            r"\bpay\s+online",
            r"\bpay\s+tuition",
            r"\b(link|url|website)\s+(to\s+)?pay",
        ],
        f"Oakton Alert: Pay and view payment options at {config.MY_OAKTON_URL}. You can also set up an installment plan there. Reply STOP to opt out.",
    ),
    (
        "cant_pay_need_time",
        [
            r"\bcan'?t\s+pay",
            r"\bneed\s+more\s+time",
            r"\binstallment",
            r"\bpayment\s+plan",
            r"\bcan\s+not\s+pay",
        ],
        f"Oakton Alert: You can set up an installment plan at {config.MY_OAKTON_URL}. If you can't attend, visit {config.WITHDRAWAL_INFO} to avoid fees. Reply STOP to opt out.",
    ),
    (
        "withdraw_drop_safe_removal",
        [
            r"\bwithdraw",
            r"\bdrop\s+(my\s+)?(class|classes)",
            r"\bcan'?t\s+attend",
            r"\bremove\s+me",
            r"\bsafe\s+removal",
            r"\bwithdrawal\s+form",
        ],
        f"Oakton Alert: To withdraw and avoid fees, visit {config.WITHDRAWAL_INFO}. That avoids being dropped for non-payment. Reply STOP to opt out.",
    ),
    (
        "when_deadline",
        [
            r"\bwhen\s+(is\s+)?(the\s+)?(deadline|due\s+date)",
            r"\bdue\s+date",
            r"\blast\s+day\s+to\s+pay",
            r"\bpayment\s+deadline",
        ],
        f"Oakton Alert: Summer payment deadline: {config.DEFAULT_DEADLINE_TEXT} Review balance at {config.MY_OAKTON_URL}. Reply STOP to opt out.",
    ),
    (
        "what_if_dropped",
        [
            r"\bdropped",
            r"\blose\s+my\s+seat",
            r"\bwhat\s+happens\s+if\s+(i'?m\s+)?dropped",
        ],
        "Oakton Alert: Pay by the deadline to keep your seat. If you don't pay, you may be dropped. Withdraw by the deadline to avoid fees. Reply STOP to opt out.",
    ),
    (
        "balance_how_much",
        [
            r"\bbalance",
            r"\bhow\s+much\s+do\s+i\s+owe",
            r"\bwhat\s+do\s+i\s+owe",
            r"\bmy\s+balance",
        ],
        f"Oakton Alert: Check your balance at {config.MY_OAKTON_URL}. Reply STOP to opt out.",
    ),
    (
        "refund_withdrawal_policy",
        [
            r"\brefund",
            r"\bwithdrawal\s+policy",
            r"\brefund\s+policy",
        ],
        f"Oakton Alert: Withdraw by the deadline for refund eligibility. For details, check {config.MY_OAKTON_URL} or contact the Cashier's Office. Reply STOP to opt out.",
    ),
]

# Precompiled regexes: (intent_id, [re.Pattern, ...], response)
INTENTS = [
    (intent_id, [re.compile(p) for p in patterns], response)
    for intent_id, patterns, response in _INTENT_SPECS
]


def match_intent(message: str) -> Tuple[str, Optional[str]]:
    """
    Match normalized message to an intent. Returns (intent_id, response).
    If no match, returns ('other', None); caller should use FALLBACK_RESPONSE.
    """
    norm = _normalize(message)
    if not norm:
        return "other", None

    for intent_id, compiled_patterns, response in INTENTS:
        for pattern in compiled_patterns:
            if pattern.search(norm):
                return intent_id, response
    return "other", None


def get_response_for_message(message: str) -> str:
    """
    Get canned response for an inbound (non-keyword) message.
    Uses intent matching; returns FALLBACK_RESPONSE for 'other'.
    """
    _, response = match_intent(message)
    return response if response is not None else messages.FALLBACK_RESPONSE
