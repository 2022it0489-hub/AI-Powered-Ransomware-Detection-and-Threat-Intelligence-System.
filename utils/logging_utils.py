import os
import datetime
import threading

# Ensure logs directory exists
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "threat_log.txt")
log_lock = threading.Lock()

def log_threat(file_path, md5_hash, confidence, classification):
    """
    Logs a detected threat to the log file in a thread-safe manner.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] THREAT DETECTED | File: {file_path} | MD5: {md5_hash} | Result: {classification} ({confidence:.2f}%) | Action: Alerted & Logged\n"
    
    with log_lock:
        try:
            with open(LOG_FILE, "a") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to threat log: {e}")

def get_recent_logs(n=20):
    """Returns the last n lines from the log file."""
    if not os.path.exists(LOG_FILE):
        return []
    
    with log_lock:
        try:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
            # Return newest first (reverse order)
            return lines[-n:][::-1]
        except Exception as e:
            print(f"Error reading logs: {e}")
            return []
