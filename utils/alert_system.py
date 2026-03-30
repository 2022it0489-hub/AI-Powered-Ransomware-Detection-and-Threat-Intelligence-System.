import smtplib
import winsound
import threading
from email.mime.text import MIMEText

class AlertSystem:
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587, email_user=None, email_pass=None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_user = email_user # Configurable
        self.email_pass = email_pass # Configurable

    def play_siren(self):
        """Plays an audio alert (Windows only)."""
        try:
            # Frequency 2500Hz, Duration 1000ms
            winsound.Beep(2500, 1000)
        except Exception as e:
            print(f"Audio alert failed: {e}")

    def send_email(self, subject, body, to_email):
        """Sends an email alert."""
        if not self.email_user or not self.email_pass:
            print("Alert System: Email credentials not set. Skipping email.")
            return

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.email_user
        msg['To'] = to_email

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_pass)
                server.sendmail(self.email_user, to_email, msg.as_string())
            print(f"Email sent to {to_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def trigger_alert(self, file_path, classification, confidence, email_recipient=None):
        """
        Triggers all configured alerts (Sound + Email).
        Runs in a separate thread to not block the main app.
        """
        def _alert_task():
            print(f"!!! ALERT !!! {classification} detected in {file_path}")
            
            # 1. Audio (Wrapped for safety)
            try:
                self.play_siren()
            except Exception as e:
                print(f"Alert System: Audio failed: {e}")
            
            # 2. Email (Wrapped for safety)
            try:
                if email_recipient:
                    subject = f"Security Alert: {classification} Detected"
                    body = (f"Threat Detected!\n\n"
                            f"File: {file_path}\n"
                            f"Classification: {classification}\n"
                            f"Confidence: {confidence:.2f}%\n"
                            f"Action: Isolate System Immediately.")
                    self.send_email(subject, body, email_recipient)
            except Exception as e:
                print(f"Alert System: Email failed: {e}")

        # Run async
        threading.Thread(target=_alert_task, daemon=True).start()

    def trigger_batch_alert(self, total, ransomware, email_recipient=None):
        """
        Triggers a summary alert for CSV batch analysis.
        """
        def _batch_alert_task():
            print(f"!!! BATCH ALERT !!! {ransomware} threats detected in {total} files")
            
            # 1. Audio (One long beep for batch completion if threats found)
            if ransomware > 0:
                try:
                    self.play_siren()
                except:
                    pass
            
            # 2. Email Summary
            try:
                if email_recipient:
                    subject = f"Security Alert: Batch Analysis Complete ({ransomware} Threats)"
                    body = (f"Security scan complete for CSV dataset.\n\n"
                            f"Total Rows Scanned: {total}\n"
                            f"Ransomware Detected: {ransomware}\n"
                            f"Benign Rows: {total - ransomware}\n\n"
                            f"Please log in to the dashboard to review the full feature breakdown.")
                    self.send_email(subject, body, email_recipient)
            except Exception as e:
                print(f"Alert System: Batch Email failed: {e}")

        threading.Thread(target=_batch_alert_task, daemon=True).start()
