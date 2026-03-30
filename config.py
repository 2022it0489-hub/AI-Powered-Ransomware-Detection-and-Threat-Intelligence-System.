"""
Configuration file for Ransomware Detection System
"""

# ============================================================================
# EMAIL ALERT CONFIGURATION
# ============================================================================

# Enable/Disable Email Alerts
EMAIL_ALERTS_ENABLED = True

# SMTP Server Settings (Gmail by default)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Email Credentials
# IMPORTANT: For Gmail, use an "App Password" not your regular password
# How to get Gmail App Password:
# 1. Enable 2-Factor Authentication on your Google Account
# 2. Go to: https://myaccount.google.com/apppasswords
# 3. Generate a new app password for "Mail"
# 4. Use that 16-character password below

EMAIL_USER = "shreyas.qriocity@gmail.com"  # Replace with your Gmail address
EMAIL_PASSWORD = "wlcn ezrs zmvp qnnt"  # Replace with your Gmail app password

# Default recipient for security alerts
ALERT_RECIPIENT = "shreyas.qriocity@gmail.com"  # Replace with recipient email

# ============================================================================
# SYSTEM CONFIGURATION
# ============================================================================

# Maximum files to scan in a directory
MAX_SCAN_FILES = 100

# Supported PE file extensions
SUPPORTED_EXTENSIONS = ('.exe', '.dll', '.sys', '.ocx', '.drv', '.scr')
