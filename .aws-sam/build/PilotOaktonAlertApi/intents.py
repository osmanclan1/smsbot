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
        f"Oakton Alert: Tuition, fees, EZ Pay, and refund info: {config.PUBLIC_TUITION_FEES_URL} "
        f"Payment schedules: {config.PUBLIC_PAYMENT_OPTIONS_URL}. "
        f"To pay or view your bill, log in at {config.MY_OAKTON_URL}. Reply STOP to opt out.",
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
        f"Oakton Alert: EZ Pay and payment plan info: {config.PUBLIC_PAYMENT_OPTIONS_URL}. "
        f"Enroll in myOakton: {config.MY_OAKTON_URL}. "
        f"If you can't attend, official withdrawal information can be found here: {config.PUBLIC_WITHDRAWAL_URL}. Reply STOP to opt out.",
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
        f"Oakton Alert: Withdrawal policy: {config.PUBLIC_WITHDRAWAL_URL}. "
        f"You can withdraw online via myOakton when applicable: {config.MY_OAKTON_URL}. "
        "Reply STOP to opt out.",
    ),
    (
        "when_deadline",
        [
            r"\bwhen\s+(is\s+)?(the\s+)?(deadline|due\s+date)",
            r"\bdue\s+date",
            r"\blast\s+day\s+to\s+pay",
            r"\bpayment\s+deadline",
        ],
        f"Oakton Alert: {config.DEFAULT_DEADLINE_TEXT} "
        f"View your bill after login: {config.MY_OAKTON_URL}. Reply STOP to opt out.",
    ),
    (
        "what_if_dropped",
        [
            r"\bdropped",
            r"\blose\s+my\s+seat",
            r"\bwhat\s+happens\s+if\s+(i'?m\s+)?dropped",
        ],
        f"Oakton Alert: Pay by the deadline to keep your seat. "
        f"Details: {config.PUBLIC_PAYMENT_OPTIONS_URL}. "
        "If you can't attend, withdraw by the refund deadline. Reply STOP to opt out.",
    ),
    (
        "balance_how_much",
        [
            r"\bbalance",
            r"\bhow\s+much\s+do\s+i\s+owe",
            r"\bwhat\s+do\s+i\s+owe",
            r"\bmy\s+balance",
        ],
        f"Oakton Alert: Your account balance is only in myOakton after login: {config.MY_OAKTON_URL}. "
        f"Published tuition rates are here: {config.PUBLIC_TUITION_FEES_URL}. Reply STOP to opt out.",
    ),
    (
        "refund_withdrawal_policy",
        [
            r"\brefund",
            r"\bwithdrawal\s+policy",
            r"\brefund\s+policy",
        ],
        f"Oakton Alert: Refund schedule and tuition info: {config.PUBLIC_TUITION_FEES_URL}. "
        f"Withdrawal: {config.PUBLIC_WITHDRAWAL_URL}. "
        "Contact the Cashier's Office with questions. Reply STOP to opt out.",
    ),
    (
        "registration_holds",
        [
            r"\bregistration\s+(open|opens|dates)",
            r"\bwhen\s+(can\s+i\s+)?register",
            r"\bhold\b",
            r"\b(have|got)\s+a\s+hold",
            r"\bcan'?t\s+register",
            r"\bwhy\s+can'?t\s+i\s+register",
            r"\bclear\s+(my\s+)?hold",
        ],
        messages.REGISTRATION_HOLDS_RESPONSE,
    ),
    (
        "financial_aid",
        [
            r"\bfinancial\s+aid",
            r"\b(aid|disbursement|disburse)\b",
            r"\bwhen\s+does\s+(aid|financial)",
            r"\baid\s+(pay|cover)",
            r"\b(my\s+)?aid\s+hasn'?t",
            r"\bwill\s+aid\s+pay",
        ],
        messages.FINANCIAL_AID_RESPONSE,
    ),
    (
        "contact_human",
        [
            r"\bwho\s+do\s+i\s+call",
            r"\b(cashier|office)\s+(number|phone)",
            r"\b(office\s+)?hours",
            r"\btalk\s+to\s+(a\s+)?(person|someone)",
            r"\b(human|representative)\b",
            r"\bcontact\s+(cashier|office)",
            r"\bphone\s+number",
            r"\bcall\s+someone",
        ],
        messages.CONTACT_HUMAN_RESPONSE,
    ),
    (
        "already_paid",
        [
            r"\b(i\s+)?already\s+paid",
            r"\bi\s+paid\s+(already|yesterday)",
            r"\bpayment\s+(didn'?t\s+go\s+through|not\s+showing)",
            r"\bpaid\s+but\s+(still|not)",
            r"\b(my\s+)?payment\s+didn'?t",
        ],
        messages.ALREADY_PAID_RESPONSE,
    ),
    (
        "what_is_oakton_alert",
        [
            r"\bwhat\s+is\s+(oakton\s+)?alert",
            r"\bwhy\s+am\s+i\s+getting\s+this",
            r"\b(i\s+)?didn'?t\s+sign\s+up",
            r"\bwhat\s+is\s+this\s+(number|service|text)",
            r"\bwhy\s+this\s+(text|message)",
        ],
        messages.WHAT_IS_OAKTON_ALERT_RESPONSE,
    ),
    (
        "myoakton_login",
        [
            r"\bcan'?t\s+log\s+in",
            r"\b(forgot|reset)\s+password",
            r"\b(log\s+in|login)\s+(problem|issue)",
            r"\b(where|how)\s+do\s+i\s+(see\s+my\s+balance|check\s+balance)\s+(on\s+the\s+)?(site|web)",
            r"\bmy\.?oakton",
            r"\b(access|log\s+into)\s+my\.?oakton",
        ],
        messages.MYOAKTON_LOGIN_RESPONSE,
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
