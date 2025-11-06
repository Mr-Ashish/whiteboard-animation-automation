"""Utilities for managing and cleaning up temporary files"""

import shutil
from pathlib import Path


class CleanupManager:
    """Context manager for handling temporary files and cleanup"""

    def __init__(self, temp_dir):
        """Initialize cleanup manager

        Args:
            temp_dir: Path to temporary directory
        """
        self.temp_dir = Path(temp_dir)
        self.temp_files = []
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def register_temp_file(self, file_path):
        """Register a temporary file for cleanup

        Args:
            file_path: Path to temporary file
        """
        self.temp_files.append(Path(file_path))

    def cleanup(self):
        """Clean up all registered temporary files and the temp directory"""
        # Remove registered temp files
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    print(f"Cleaned up: {temp_file}")
            except Exception as e:
                print(f"Warning: Could not delete {temp_file}: {e}")

        # Clean the entire temp directory
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            print(f"Warning: Could not delete temp directory {self.temp_dir}: {e}")

    def __enter__(self):
        """Enter context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and cleanup"""
        self.cleanup()
        return False


def ensure_output_dir(output_path):
    """Ensure the output directory exists

    Args:
        output_path: Path to output file

    Returns:
        Path: The output path
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path
