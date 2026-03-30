# Email Alert Setup Guide

This guide explains how to configure email alerts for the Ransomware Detection System.

## Prerequisites

- A Gmail account (or other SMTP-compatible email service)
- 2-Factor Authentication enabled on your Google account (for Gmail)

## Step 1: Generate Gmail App Password

Since Gmail requires secure authentication, you need to create an "App Password":

1. **Enable 2-Factor Authentication** (if not already enabled):
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Under "Signing in to Google", enable "2-Step Verification"

2. **Generate App Password**:
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" as the app
   - Select "Windows Computer" (or your device)
   - Click "Generate"
   - Copy the 16-character password (it will look like: `xxxx xxxx xxxx xxxx`)

## Step 2: Configure Email Settings

1. Open `config.py` in the project root directory

2. Update the following settings:

```python
# Enable email alerts
EMAIL_ALERTS_ENABLED = True

# Your Gmail address
EMAIL_USER = "your-email@gmail.com"

# The 16-character app password (remove spaces)
EMAIL_PASSWORD = "xxxxxxxxxxxxxxxx"

# Who should receive alerts
ALERT_RECIPIENT = "security-team@example.com"
```

3. Save the file

## Step 3: Test Email Alerts

1. Start the application:
   ```bash
   python app.py
   ```

2. Look for the confirmation message:
   ```
   ✓ Alert System initialized with email support
   ```

3. Scan a test file or directory that contains ransomware samples

4. Check the recipient's inbox for alert emails

## Email Alert Content

When ransomware is detected, the email will include:

- **Subject**: "Security Alert: Ransomware Detected"
- **Body**:
  - File path
  - Classification (Ransomware)
  - Confidence percentage
  - Timestamp
  - Recommended action

## Troubleshooting

### Email not sending

**Issue**: "Alert System: Email credentials not set. Skipping email."
- **Solution**: Verify `EMAIL_USER` and `EMAIL_PASSWORD` are set in `config.py`

**Issue**: "Failed to send email: Authentication failed"
- **Solution**: 
  - Verify you're using an App Password, not your regular Gmail password
  - Ensure 2-Factor Authentication is enabled
  - Check that the app password is entered correctly (no spaces)

**Issue**: "Failed to send email: Connection refused"
- **Solution**: 
  - Check your internet connection
  - Verify firewall isn't blocking port 587
  - Ensure `SMTP_SERVER` and `SMTP_PORT` are correct

### Email going to spam

- Add the sender email to your contacts
- Mark the email as "Not Spam"
- Create a filter to always deliver these emails to inbox

## Using Other Email Providers

If you want to use a different email provider (not Gmail), update these settings in `config.py`:

### Outlook/Hotmail
```python
SMTP_SERVER = "smtp-mail.outlook.com"
SMTP_PORT = 587
```

### Yahoo Mail
```python
SMTP_SERVER = "smtp.mail.yahoo.com"
SMTP_PORT = 587
```

### Custom SMTP Server
```python
SMTP_SERVER = "your-smtp-server.com"
SMTP_PORT = 587  # or 465 for SSL
```

## Security Best Practices

1. **Never commit credentials to version control**
   - Add `config.py` to `.gitignore`
   - Use environment variables for production deployments

2. **Restrict app password access**
   - Only use app passwords for this specific application
   - Revoke app passwords when no longer needed

3. **Monitor alert emails**
   - Set up email filters for security alerts
   - Ensure alerts go to a monitored inbox

## Disabling Email Alerts

To disable email alerts temporarily:

```python
EMAIL_ALERTS_ENABLED = False
```

The system will still play audio alerts but won't send emails.
