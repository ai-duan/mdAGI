"""
Log capture utility for streaming Agent output to the UI.
"""

import sys
import threading
from typing import TextIO


class UILogCapture:
    """Captures stdout/stderr output for display in the UI."""
    
    def __init__(self):
        self.logs: list[str] = []
        self._lock = threading.Lock()
        self._original_stdout: TextIO | None = None
        self._original_stderr: TextIO | None = None
    
    def write(self, msg: str) -> int:
        """Write a message to the log buffer (thread-safe)."""
        with self._lock:
            if msg.strip():  # Only store non-empty messages
                self.logs.append(msg)
        return len(msg)
    
    def flush(self) -> None:
        """Flush method for compatibility with file-like interface."""
        pass
    
    def get_logs(self) -> str:
        """Get all captured logs as a single string."""
        with self._lock:
            return "\n".join(self.logs)
    
    def clear(self) -> None:
        """Clear all captured logs."""
        with self._lock:
            self.logs.clear()
    
    def __enter__(self) -> "UILogCapture":
        """Context manager entry: redirect stdout/stderr."""
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit: restore stdout/stderr."""
        if self._original_stdout:
            sys.stdout = self._original_stdout
        if self._original_stderr:
            sys.stderr = self._original_stderr
        self._original_stdout = None
        self._original_stderr = None
