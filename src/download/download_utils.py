"""Utilities for downloading images from URLs"""

import requests
import hashlib
from pathlib import Path
from urllib.parse import urlparse
# Relative import for grouped structure
from ..config.config import TEMP_DIR


def is_url(path_or_url):
    """Check if a string is a URL

    Args:
        path_or_url: String to check

    Returns:
        bool: True if it's a URL, False otherwise
    """
    try:
        result = urlparse(str(path_or_url))
        return all([result.scheme, result.netloc])
    except:
        return False


def download_image(url, cleanup_manager=None):
    """Download an image from a URL to a temporary file

    Args:
        url: URL of the image to download
        cleanup_manager: Optional CleanupManager instance to register temp file

    Returns:
        Path: Path to the downloaded temporary file

    Raises:
        ValueError: If download fails or URL is invalid
    """
    if not is_url(url):
        raise ValueError(f"Invalid URL: {url}")

    try:
        # Get file extension from URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        ext = Path(path).suffix if Path(path).suffix else '.jpg'

        # Create unique filename using URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"downloaded_{url_hash}{ext}"

        # Use configured temp directory
        temp_dir = TEMP_DIR
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / filename

        # Download the image
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()

        # Write content to file (silent download to reduce log spam; success shown in video creation)
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Register for cleanup if manager provided
        if cleanup_manager:
            cleanup_manager.register_temp_file(temp_path)

        return temp_path

    except requests.RequestException as e:
        raise ValueError(f"Failed to download image from {url}: {e}")


def download_audio(url, cleanup_manager=None):
    """Download an audio file from a URL to a temporary file

    Args:
        url: URL of the audio file to download
        cleanup_manager: Optional CleanupManager instance to register temp file

    Returns:
        Path: Path to the downloaded temporary file

    Raises:
        ValueError: If download fails or URL is invalid
    """
    if not is_url(url):
        raise ValueError(f"Invalid URL: {url}")

    try:
        # Get file extension from URL or default to mp3
        parsed_url = urlparse(url)
        path = parsed_url.path
        ext = Path(path).suffix if Path(path).suffix else '.mp3'

        # Create unique filename using URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"audio_{url_hash}{ext}"

        # Use configured temp directory
        temp_dir = TEMP_DIR
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / filename

        # Download the audio file
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()

        # Write content to file (silent download to reduce log spam; success shown in video creation)
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Register for cleanup if manager provided
        if cleanup_manager:
            cleanup_manager.register_temp_file(temp_path)

        return temp_path

    except requests.RequestException as e:
        raise ValueError(f"Failed to download audio from {url}: {e}")


def resolve_image_path(path_or_url, cleanup_manager=None):
    """Resolve an image path or URL to a local file path

    Args:
        path_or_url: Either a local file path or a URL
        cleanup_manager: Optional CleanupManager instance for temp file cleanup

    Returns:
        Path: Local file path (downloaded if URL)
    """
    if is_url(path_or_url):
        return download_image(path_or_url, cleanup_manager)
    else:
        return Path(path_or_url)


def resolve_audio_path(path_or_url, cleanup_manager=None):
    """Resolve an audio path or URL to a local file path

    Args:
        path_or_url: Either a local file path or a URL
        cleanup_manager: Optional CleanupManager instance for temp file cleanup

    Returns:
        Path: Local file path (downloaded if URL)
    """
    if is_url(path_or_url):
        return download_audio(path_or_url, cleanup_manager)
    else:
        return Path(path_or_url)
