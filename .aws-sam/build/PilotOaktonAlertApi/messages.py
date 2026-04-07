"""
Oakton Alert pilot – all canned messages and trigger templates.
"""
import config

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
        f"Details: {config.PUBLIC_REGISTER_FOR_CLASSES_URL}. "
        f"Review payment options at {config.PUBLIC_PAYMENT_OPTIONS_URL}. "
        f"Log in to {config.MY_OAKTON_URL} to view your bill or pay. "
        "Reply STOP to opt out."
    ),
    "payment_deadline_final": (
        "Oakton Alert Final Notice: The Summer semester payment deadline is tomorrow. "
        f"Payment schedules: {config.PUBLIC_PAYMENT_OPTIONS_URL}. "
        f"Log in to {config.MY_OAKTON_URL} to pay or set up EZ Pay. "
        f"If you can't attend, official withdrawal information can be found here: {config.PUBLIC_WITHDRAWAL_URL}. Reply STOP to opt out."
    ),
    "payment_deadline_reminder": (
        "Oakton Alert: Your Summer semester payment deadline is in {days} days. "
        f"Payment options and deadlines: {config.PUBLIC_PAYMENT_OPTIONS_URL}. "
        f"Log in to {config.MY_OAKTON_URL} to pay or review your bill. "
        f"If you can't attend, official withdrawal information can be found here: {config.PUBLIC_WITHDRAWAL_URL}. Reply STOP to opt out."
    ),
}

FALLBACK_RESPONSE = (
    f"Oakton Alert: Tuition & payment info: {config.PUBLIC_TUITION_FEES_URL} "
    f"Payment options: {config.PUBLIC_PAYMENT_OPTIONS_URL}. "
    f"Service help: {config.HELP_SITE_URL}. Reply HELP for more options."
)
OPTED_OUT_REPLY = (
    "Oakton Alert: You're opted out of tuition reminders. Reply START to re-enroll."
)

# Intent-based responses (registration, financial aid, contact, already paid, what is this, MyOakton/login)
REGISTRATION_HOLDS_RESPONSE = (
    f"Oakton Alert: {config.REGISTRATION_INFO} Reply STOP to opt out."
)
FINANCIAL_AID_RESPONSE = (
    f"Oakton Alert: {config.FINANCIAL_AID_INFO} Reply STOP to opt out."
)
CONTACT_HUMAN_RESPONSE = (
    f"Oakton Alert: {config.CASHIER_CONTACT} "
    f"For help with this SMS service, visit {config.HELP_SITE_URL} or email {config.HELP_EMAIL}. Reply STOP to opt out."
)
ALREADY_PAID_RESPONSE = (
    f"Oakton Alert: Payments may take 1-2 business days to post. "
    f"Log in to {config.MY_OAKTON_URL} to check your account. "
    f"Payment FAQs: {config.PUBLIC_PAYMENT_OPTIONS_URL}. "
    "If it still looks wrong, contact the Cashier's Office. Reply STOP to opt out."
)
WHAT_IS_OAKTON_ALERT_RESPONSE = (
    "Oakton Alert: Automated tuition reminders from the Cashier's Office. "
    "Reply STOP to opt out, START to re-enroll, HELP for more options."
)
MYOAKTON_LOGIN_RESPONSE = (
    f"Oakton Alert: Log in at {config.MY_OAKTON_URL} for your student account. "
    f"Tuition & payment overview: {config.PUBLIC_TUITION_FEES_URL}. "
    f"General SMS help: {config.HELP_SITE_URL}. Reply STOP to opt out."
)
