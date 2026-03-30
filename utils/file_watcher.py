import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RansomwareFileWatcher(FileSystemEventHandler):
    """
    File system event handler for monitoring new files in a directory.
    Automatically triggers scanning when new PE files are detected.
    """
    
    # Supported PE file extensions
    SUPPORTED_EXTENSIONS = ('.exe', '.dll', '.sys', '.ocx', '.drv', '.scr')
    
    def __init__(self, scan_callback, socketio=None):
        """
        Initialize the file watcher.
        
        Args:
            scan_callback: Function to call when a new file is detected
            socketio: Optional SocketIO instance for emitting events
        """
        super().__init__()
        self.scan_callback = scan_callback
        self.socketio = socketio
        self.files_scanned = 0
        
    def on_created(self, event):
        """
        Called when a file or directory is created.
        
        Args:
            event: FileSystemEvent object containing event details
        """
        # Ignore directory creation events
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Check if file has a supported extension
        if not self._is_supported_file(file_path):
            print(f"[WATCHER] Ignoring non-PE file: {file_path}")
            return
        
        # Wait a moment to ensure file is fully written
        time.sleep(0.5)
        
        # Check if file still exists and is accessible
        if not os.path.exists(file_path):
            print(f"[WATCHER] File disappeared: {file_path}")
            return
        
        print(f"[WATCHER] New file detected: {file_path}")
        
        # Emit event via WebSocket if available
        if self.socketio:
            self.socketio.emit('file_detected', {
                'path': file_path,
                'filename': os.path.basename(file_path)
            })
        
        # Trigger the scan callback
        try:
            self.scan_callback(file_path)
            self.files_scanned += 1
        except Exception as e:
            print(f"[WATCHER ERROR] Failed to scan {file_path}: {e}")
            if self.socketio:
                self.socketio.emit('scan_error', {
                    'path': file_path,
                    'error': str(e)
                })
    
    def _is_supported_file(self, filepath):
        """Check if file has a supported PE extension."""
        return filepath.lower().endswith(self.SUPPORTED_EXTENSIONS)


class FolderMonitor:
    """
    Manager class for folder monitoring with watchdog.
    Handles starting, stopping, and status of the file watcher.
    """
    
    def __init__(self):
        self.observer = None
        self.handler = None
        self.monitored_path = None
        self.is_monitoring = False
        
    def start_monitoring(self, path, scan_callback, socketio=None):
        """
        Start monitoring a folder for new files.
        
        Args:
            path: Directory path to monitor
            scan_callback: Function to call when new files are detected
            socketio: Optional SocketIO instance
            
        Returns:
            tuple: (success: bool, message: str)
        """
        # Validate path
        if not os.path.exists(path):
            return False, f"Path does not exist: {path}"
        
        if not os.path.isdir(path):
            return False, f"Path is not a directory: {path}"
        
        # Stop existing monitoring if any
        if self.is_monitoring:
            self.stop_monitoring()
        
        try:
            # Create handler and observer
            self.handler = RansomwareFileWatcher(scan_callback, socketio)
            self.observer = Observer()
            self.observer.schedule(self.handler, path, recursive=True)
            
            # Start the observer
            self.observer.start()
            
            self.monitored_path = path
            self.is_monitoring = True
            
            print(f"[MONITOR] Started monitoring: {path}")
            return True, f"Monitoring started: {path}"
            
        except Exception as e:
            print(f"[MONITOR ERROR] Failed to start monitoring: {e}")
            return False, f"Failed to start monitoring: {str(e)}"
    
    def stop_monitoring(self):
        """
        Stop the current monitoring session.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_monitoring:
            return False, "No active monitoring session"
        
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=2)
            
            files_scanned = self.handler.files_scanned if self.handler else 0
            
            self.observer = None
            self.handler = None
            self.monitored_path = None
            self.is_monitoring = False
            
            print(f"[MONITOR] Stopped monitoring. Files scanned: {files_scanned}")
            return True, f"Monitoring stopped. Scanned {files_scanned} files."
            
        except Exception as e:
            print(f"[MONITOR ERROR] Error stopping monitoring: {e}")
            return False, f"Error stopping monitoring: {str(e)}"
    
    def get_status(self):
        """
        Get current monitoring status.
        
        Returns:
            dict: Status information
        """
        return {
            'is_monitoring': self.is_monitoring,
            'monitored_path': self.monitored_path,
            'files_scanned': self.handler.files_scanned if self.handler else 0
        }
