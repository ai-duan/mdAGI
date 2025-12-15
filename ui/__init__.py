"""
Genesis Agent Gradio Web UI Module

This module provides a web-based interface for the Genesis Agent system,
replacing the command-line interface with a more intuitive graphical interface.
"""

from ui.service import AgentUIService
from ui.logger import UILogCapture
from ui.errors import safe_execute, safe_execute_generator, format_error, UIError

__all__ = [
    "AgentUIService", 
    "UILogCapture",
    "safe_execute",
    "safe_execute_generator", 
    "format_error",
    "UIError",
]
