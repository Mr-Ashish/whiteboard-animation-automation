"""Audio processing utilities for adding background music to videos"""

import subprocess
from pathlib import Path

# Colored logging for differentiation
from ..utils.log_utils import log_success


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

        log_success(f"✓ Background music added: {output_path}")
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


def get_media_duration(media_path):
    """Get duration of a media file (video or audio) using ffprobe

    Args:
        media_path: Path to media file

    Returns:
        float: Duration in seconds
    """
    media_path = Path(media_path)

    probe_cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(media_path)
    ]

    try:
        probe_result = subprocess.run(
            probe_cmd,
            check=True,
            capture_output=True,
            text=True
        )
        return float(probe_result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to get media duration: {e.stderr}")
    except FileNotFoundError:
        raise FileNotFoundError("ffprobe not found. Please install ffmpeg")


def loop_audio_to_video_length(video_path, audio_path, output_path=None, volume=1.0, fadeout_duration=1.0):
    """Add background music that loops to match video duration with smooth fadeout

    Args:
        video_path: Path to the input video file
        audio_path: Path to the audio file (mp3, wav, etc.)
        output_path: Path to output video (optional)
        volume: Audio volume multiplier (0.0 to 1.0, default 1.0)
        fadeout_duration: Duration of fadeout in seconds (default 1.0)

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
        # Get video duration
        video_duration = get_media_duration(video_path)
        fadeout_start = max(0, video_duration - fadeout_duration)

        print(f"Video duration: {video_duration:.2f}s, fadeout at {fadeout_start:.2f}s")

        # FFmpeg command with audio looping and fadeout
        # afade: audio fadeout filter starting at video_duration - fadeout_duration
        audio_filter = f'volume={volume},afade=t=out:st={fadeout_start}:d={fadeout_duration}'

        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-stream_loop', '-1',       # Loop audio infinitely
            '-i', str(audio_path),
            '-c:v', 'copy',
            '-filter:a', audio_filter,
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

        log_success(f"✓ Looped background music added with fadeout: {output_path}")
        return output_path

    except subprocess.CalledProcessError as e:
        print(f"Error adding background music: {e.stderr}")
        raise ValueError(f"FFmpeg failed to add audio: {e.stderr}")
    except FileNotFoundError:
        raise FileNotFoundError(
            "ffmpeg not found. Please install ffmpeg"
        )


def match_video_to_audio_length(video_path, audio_path, output_path=None, volume=1.0):
    """Add audio to video, extending video with last frame if audio is longer

    This ensures all audio content is preserved by extending the video duration
    to match the audio duration if needed.

    Args:
        video_path: Path to the input video file
        audio_path: Path to the audio file (mp3, wav, etc.)
        output_path: Path to output video (optional)
        volume: Audio volume multiplier (0.0 to 1.0, default 1.0)

    Returns:
        Path: Path to the output video with audio
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
        # Get durations
        video_duration = get_media_duration(video_path)
        audio_duration = get_media_duration(audio_path)

        print(f"Video duration: {video_duration:.2f}s")
        print(f"Audio duration: {audio_duration:.2f}s")

        if audio_duration > video_duration:
            # Audio is longer - extend video to match audio
            extra_time = audio_duration - video_duration
            print(f"Extending video by {extra_time:.2f}s to match audio duration")

            # Use tpad filter to extend video by duplicating last frame
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-stream_loop', '-1',       # Loop audio infinitely
                '-i', str(audio_path),
                '-filter_complex', f'[0:v]tpad=stop_mode=clone:stop_duration={extra_time}[v]',
                '-map', '[v]',
                '-map', '1:a:0',
                '-filter:a', f'volume={volume}',
                '-shortest',                # Stop when audio ends (now longer than video)
                '-c:v', 'libx264',          # Re-encode video to extend it
                '-preset', 'medium',
                '-crf', '23',
                str(output_path)
            ]
        else:
            # Video is longer or equal - just add audio with looping
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

        log_success(f"✓ Audio added successfully: {output_path}")
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
