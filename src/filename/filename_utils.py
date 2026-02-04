from datetime import datetime
import uuid


def generate_timestamped_filename(extension=".mp4"):
    """
    Generate filename with format: YYYY-MM-DD_HH-MM-SS_{uuid}.mp4
    Example: 2025-12-23_14-30-25_f47ac10b.mp4

    Args:
        extension (str): File extension to use (default: ".mp4")

    Returns:
        str: Timestamped filename with short UUID
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_id = str(uuid.uuid4())[:8]  # Use short UUID (first 8 chars)
    return f"{timestamp}_{unique_id}{extension}"
