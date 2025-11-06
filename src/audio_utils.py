"""Audio processing utilities for adding background music to videos"""

import subprocess
from pathlib import Path


def add_background_music(video_path, audio_path, output_path=None, volume=1.0):
    """Add background music to a video using ffmpeg

    Args:
        video_path: Path to the input video file
        audio_path: Path to the audio file (mp3, wav, etc.)
        output_path: Path to output video (optional, defaults to video_path with _music suffix)
        volume: Audio volume multiplier (0.0 to 1.0, default 1.0)

    Returns:
        Path: Path to the output video with audio

    Raises:
        FileNotFoundError: If ffmpeg is not installed
        ValueError: If input files don't exist
    """
    video_path = Path(video_path)
    audio_path = Path(audio_path)

    if not video_path.exists():
        raise ValueError(f"Video file not found: {video_path}")
    if not audio_path.exists():
        raise ValueError(f"Audio file not found: {audio_path}")

    # Determine output path
    if output_path is None:
        output_path = video_path.parent / f"{video_path.stem}_music{video_path.suffix}"
    else:
        output_path = Path(output_path)

    print(f"\nAdding background music: {audio_path.name}")
    print(f"Volume level: {volume}")

    try:
        # FFmpeg command to add audio to video
        # -shortest: finish encoding when shortest input stream ends
        # -filter:a: audio filter for volume adjustment
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),      # Input video
            '-i', str(audio_path),      # Input audio
            '-c:v', 'copy',             # Copy video codec (no re-encode)
            '-filter:a', f'volume={volume}',  # Adjust volume
            '-shortest',                # Match video duration
            '-map', '0:v:0',           # Map video from first input
            '-map', '1:a:0',           # Map audio from second input
            str(output_path)
        ]

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        print(f"✓ Background music added: {output_path}")
        return output_path

    except subprocess.CalledProcessError as e:
        print(f"Error adding background music: {e.stderr}")
        raise ValueError(f"FFmpeg failed to add audio: {e.stderr}")
    except FileNotFoundError:
        raise FileNotFoundError(
            "ffmpeg not found. Please install ffmpeg:\n"
            "  macOS: brew install ffmpeg\n"
            "  Ubuntu: sudo apt install ffmpeg\n"
            "  Windows: Download from https://ffmpeg.org/"
        )


def loop_audio_to_video_length(video_path, audio_path, output_path=None, volume=1.0):
    """Add background music that loops to match video duration

    Args:
        video_path: Path to the input video file
        audio_path: Path to the audio file (mp3, wav, etc.)
        output_path: Path to output video (optional)
        volume: Audio volume multiplier (0.0 to 1.0, default 1.0)

    Returns:
        Path: Path to the output video with looped audio
    """
    video_path = Path(video_path)
    audio_path = Path(audio_path)

    if not video_path.exists():
        raise ValueError(f"Video file not found: {video_path}")
    if not audio_path.exists():
        raise ValueError(f"Audio file not found: {audio_path}")

    # Determine output path
    if output_path is None:
        output_path = video_path.parent / f"{video_path.stem}_music{video_path.suffix}"
    else:
        output_path = Path(output_path)

    print(f"\nAdding looped background music: {audio_path.name}")
    print(f"Volume level: {volume}")

    try:
        # FFmpeg command with audio looping
        # astream=loop: loop audio stream
        # volume filter: adjust volume
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-stream_loop', '-1',       # Loop audio infinitely
            '-i', str(audio_path),
            '-c:v', 'copy',
            '-filter:a', f'volume={volume}',
            '-shortest',                # Stop when video ends
            '-map', '0:v:0',
            '-map', '1:a:0',
            str(output_path)
        ]

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        print(f"✓ Looped background music added: {output_path}")
        return output_path

    except subprocess.CalledProcessError as e:
        print(f"Error adding background music: {e.stderr}")
        raise ValueError(f"FFmpeg failed to add audio: {e.stderr}")
    except FileNotFoundError:
        raise FileNotFoundError(
            "ffmpeg not found. Please install ffmpeg"
        )


def get_terminal_command(video_path, audio_path, output_path=None, loop=False, volume=1.0):
    """Get the terminal command for adding audio manually

    Args:
        video_path: Path to video file
        audio_path: Path to audio file
        output_path: Path to output file
        loop: Whether to loop the audio
        volume: Volume level (0.0 to 1.0)

    Returns:
        str: FFmpeg command to run in terminal
    """
    if output_path is None:
        video_path = Path(video_path)
        output_path = video_path.parent / f"{video_path.stem}_music{video_path.suffix}"

    if loop:
        cmd = (
            f"ffmpeg -i {video_path} -stream_loop -1 -i {audio_path} "
            f"-c:v copy -filter:a 'volume={volume}' -shortest "
            f"-map 0:v:0 -map 1:a:0 {output_path}"
        )
    else:
        cmd = (
            f"ffmpeg -i {video_path} -i {audio_path} "
            f"-c:v copy -filter:a 'volume={volume}' -shortest "
            f"-map 0:v:0 -map 1:a:0 {output_path}"
        )

    return cmd
