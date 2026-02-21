"""
Oakton Alert pilot – config (URLs, deadline text). Override via env.
"""
import os

MY_OAKTON_URL = os.getenv("OAKTON_ALERT_MY_OAKTON_URL", "my.oakton.edu")
HELP_SITE_URL = os.getenv("OAKTON_ALERT_HELP_URL", "oaktonalert.com")
HELP_EMAIL = os.getenv("OAKTON_ALERT_HELP_EMAIL", "info@oaktonalert.com")
DEFAULT_DEADLINE_TEXT = os.getenv("OAKTON_ALERT_DEADLINE_TEXT", "Check my.oakton.edu for the exact date.")
WITHDRAWAL_INFO = os.getenv("OAKTON_ALERT_WITHDRAWAL_INFO", "the Oakton Withdrawal form")
