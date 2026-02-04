"""Colored logging utilities for terminal differentiation.
Supports info (default), success (green), warning (yellow), error (red).
"""
import sys


def color_text(text, color_code):
    """Wrap text with ANSI color code (works in most terminals)."""
    colors = {
        'red': 31,      # Errors
        'green': 32,    # Success
        'yellow': 33,   # Warnings
        'blue': 34,     # Info
        'reset': 0
    }
    return f"\033[{colors.get(color_code, 0)}m{text}\033[0m"


def log_info(msg):
    """Standard log (white/default)."""
    print(msg)


def log_success(msg):
    """Success log (green)."""
    print(color_text(msg, 'green'))


def log_warning(msg):
    """Warning log (yellow)."""
    print(color_text(f"Warning: {msg}", 'yellow'))


def log_error(msg):
    """Error log (red) - also exits."""
    print(color_text(f"Error: {msg}", 'red'))
    sys.exit(1)
