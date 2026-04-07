"""
Oakton Alert pilot – config (URLs, deadline text). Override via env.

Public oakton.edu pages are readable without login. my.oakton.edu is the student
portal (login required for balance, payment, and your schedule).
"""
import os


def _https_url(host_or_url: str) -> str:
    h = (host_or_url or "").strip()
    if not h:
        return h
    if h.startswith("http://") or h.startswith("https://"):
        return h
    return f"https://{h}"


# Student portal — login required for bill, balance, paying, concise schedule
MY_OAKTON_URL = _https_url(os.getenv("OAKTON_ALERT_MY_OAKTON_URL", "my.oakton.edu"))

# Public informational pages (no login required)
PUBLIC_TUITION_FEES_URL = os.getenv(
    "OAKTON_ALERT_PUBLIC_TUITION_FEES_URL",
    "https://www.oakton.edu/paying-for-college/tuition-and-fees.php",
)
PUBLIC_PAYMENT_OPTIONS_URL = os.getenv(
    "OAKTON_ALERT_PUBLIC_PAYMENT_OPTIONS_URL",
    "https://www.oakton.edu/paying-for-college/payment-options.php",
)
PUBLIC_FINANCIAL_AID_URL = os.getenv(
    "OAKTON_ALERT_PUBLIC_FINANCIAL_AID_URL",
    "https://www.oakton.edu/paying-for-college/financial-aid/index.php",
)
PUBLIC_WITHDRAWAL_URL = os.getenv(
    "OAKTON_ALERT_PUBLIC_WITHDRAWAL_URL",
    "https://www.oakton.edu/admissions/withdrawal-from-classes.php",
)
PUBLIC_REGISTER_FOR_CLASSES_URL = os.getenv(
    "OAKTON_ALERT_PUBLIC_REGISTER_FOR_CLASSES_URL",
    "https://www.oakton.edu/admissions/register-for-classes.php",
)

HELP_SITE_URL = os.getenv("OAKTON_ALERT_HELP_URL", "oaktonalert.com")
HELP_EMAIL = os.getenv("OAKTON_ALERT_HELP_EMAIL", "info@oaktonalert.com")
DEFAULT_DEADLINE_TEXT = os.getenv(
    "OAKTON_ALERT_DEADLINE_TEXT",
    f"See payment due dates for your term at {PUBLIC_PAYMENT_OPTIONS_URL}.",
)
REGISTRATION_INFO = os.getenv(
    "OAKTON_ALERT_REGISTRATION_INFO",
    f"Registration info: {PUBLIC_REGISTER_FOR_CLASSES_URL}. "
    f"Log in to {MY_OAKTON_URL} to view holds or register.",
)
FINANCIAL_AID_INFO = os.getenv(
    "OAKTON_ALERT_FINANCIAL_AID_INFO",
    f"Financial aid: {PUBLIC_FINANCIAL_AID_URL}. "
    f"Log in to {MY_OAKTON_URL} to view your award and how it applies to your bill.",
)
CASHIER_CONTACT = os.getenv(
    "OAKTON_ALERT_CASHIER_CONTACT",
    "Cashier's Office: 847.635.1639 or cashier@oakton.edu. "
    "Enrollment Center: 847.635.1700.",
)
