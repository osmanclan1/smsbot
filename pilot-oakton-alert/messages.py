"""
Oakton Alert pilot – all canned messages and trigger templates.
"""

OPT_IN_RESPONSE = (
    "Oakton Alert: You are enrolled in automated tuition reminders from the Cashier's Office. "
    "Reply STOP to opt out, HELP for info."
)
OPT_OUT_RESPONSE = (
    "Oakton Alert: You have successfully opted out and will no longer receive tuition reminders via SMS. "
    "To re-enroll, reply START at any time."
)
HELP_RESPONSE = (
    "Oakton Alert: For assistance with this automated service, please visit oaktonalert.com or email info@oaktonalert.com."
)

TRIGGER_MESSAGES = {
    "registration_opens": (
        "Oakton Alert: Hello, Summer registration is now open! "
        "To secure your classes and avoid being dropped for non-payment, please review your balance at my.oakton.edu. "
        "Reply STOP to opt out."
    ),
    "payment_deadline_final": (
        "Oakton Alert Final Notice: The Summer semester payment deadline is tomorrow. "
        "To avoid being dropped from your classes and losing your seat, please finalize your payment or installment plan at my.oakton.edu. "
        "If you can no longer attend, please visit the Oakton Withdrawal form to avoid fees. Reply STOP to opt out."
    ),
    "payment_deadline_reminder": (
        "Oakton Alert: Your Summer semester payment deadline is in {days} days. "
        "To avoid being dropped for non-payment, review your balance and payment options at my.oakton.edu. "
        "If you can't attend, visit the Oakton Withdrawal form to avoid fees. Reply STOP to opt out."
    ),
}

FALLBACK_RESPONSE = (
    "Oakton Alert: For balance, payment, or withdrawal help, visit my.oakton.edu or oaktonalert.com. Reply HELP for more options."
)
OPTED_OUT_REPLY = (
    "Oakton Alert: You're opted out of tuition reminders. Reply START to re-enroll."
)
