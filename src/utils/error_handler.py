from .log_utils import log_error


def handle_error(message, exit_code=1):
    """Standardized error handling (delegates to colored log_error)."""
    log_error(message)  # Always exits; exit_code ignored for simplicity
