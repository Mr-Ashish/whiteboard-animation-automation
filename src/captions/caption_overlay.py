"""Caption overlay: draw timed text (word/letter) on video frames with Pillow.

Supports TrueType (.ttf) and OpenType (.otf) fonts via font_path or src/assets/fonts/.

Each frame shows the current word (per timing); optional pop-scale on appear + 
highlighted_words array (with custom color) from captions JSON config.
"""

import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Union

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Relative import for grouped structure
from ..config.config import PROJECT_ROOT


# Default options for caption styling (white text, black outline).
# Only one line is drawn: the current segment for this frame's time.
DEFAULT_CAPTION_OPTIONS = {
    "font_path": None,           # Path to .ttf or .otf; None = try bundled or system font
    "font_size_normal": 24,     # Unused (kept for optional second-line use)
    "font_size_emphasized": 46, # Font size for the current word/letter
    "stroke_width": 3,
    "fill_color": (255, 255, 255),
    "stroke_color": (0, 0, 0),
    "line1_y_ratio": 0.12,       # Unused (no constant top line)
    "line2_y_ratio": 0.5,       # Vertical position of the current word (fraction of height)
    "show_emphasized": True,    # If False, no text is drawn
    "word_separator": " ",      # Used when building full_text in _get_current_segment
    # Pop animation for each word (scale from small to full; timing unchanged)
    "pop_effect": True,
    "pop_scale_start": 0.6,     # Start at 60% size
    "pop_duration_ratio": 0.25, # Pop over first 25% of word duration
    # Highlighted words (list; if current word matches, use highlight_color)
    "highlighted_words": [],    # e.g. ["key", "term"]
    "highlight_color": (255, 215, 0),  # Gold RGB default
}


def _get_font(path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
    """Load a TrueType or OpenType font (.ttf or .otf) at given size. Fallback to default if path missing."""
    # Try user-provided path first
    if path:
        p = Path(path)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                pass
    # Try bundled fonts (src/assets/fonts/) — any .ttf or .otf
    assets_fonts = PROJECT_ROOT / "src" / "assets" / "fonts"
    if assets_fonts.is_dir():
        for ext in ("*.ttf", "*.otf"):
            for try_path in sorted(assets_fonts.glob(ext)):
                try:
                    return ImageFont.truetype(str(try_path), size)
                except OSError:
                    continue
    # Try common system paths (Linux/Raspberry Pi)
    for try_path in [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/opentype/dejavu/DejaVuSans-Bold.otf"),
    ]:
        if try_path.exists():
            try:
                return ImageFont.truetype(str(try_path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def alignment_to_word_segments(
    characters: List[str],
    character_start_times_seconds: List[float],
    character_end_times_seconds: List[float],
    text: Optional[str] = None,
) -> List[Tuple[str, float, float]]:
    """Convert ElevenLabs-style character alignment to word-level segments.

    Groups consecutive characters into words (split on whitespace). Each segment
    is (word, start_sec, end_sec) where start/end come from the first/last
    character of that word in the alignment arrays.

    Args:
        characters: List of single-character strings (from alignment.characters).
        character_start_times_seconds: Start time per character (same length as characters).
        character_end_times_seconds: End time per character (same length as characters).
        text: Optional original text; if provided and len(text) == len(characters),
              word display uses this (e.g. to show "2" instead of normalized "two").

    Returns:
        List of (word, start_sec, end_sec) for overlay.
    """
    n = len(characters)
    if n == 0:
        return []
    if len(character_start_times_seconds) != n or len(character_end_times_seconds) != n:
        raise ValueError(
            "alignment arrays must have same length: "
            f"characters={n}, starts={len(character_start_times_seconds)}, ends={len(character_end_times_seconds)}"
        )
    # Use provided text for word display only when length matches
    use_text = text is not None and len(text) == n
    segments = []
    i = 0
    while i < n:
        # Skip whitespace
        while i < n and characters[i].strip() == "":
            i += 1
        if i >= n:
            break
        start_idx = i
        word_chars = []
        while i < n and characters[i].strip() != "":
            word_chars.append(characters[i])
            i += 1
        end_idx = i - 1
        word = "".join(word_chars) if not use_text else text[start_idx : end_idx + 1]
        if word:
            segments.append(
                (
                    word,
                    character_start_times_seconds[start_idx],
                    character_end_times_seconds[end_idx],
                )
            )
    return segments


def _is_elevenlabs_alignment_payload(data: Any) -> bool:
    """True if data looks like ElevenLabs timing-only payload (has alignment with character arrays)."""
    if not isinstance(data, dict):
        return False
    align = data.get("alignment") or data.get("normalized_alignment")
    if not isinstance(align, dict):
        return False
    chars = align.get("characters")
    starts = align.get("character_start_times_seconds")
    ends = align.get("character_end_times_seconds")
    return (
        isinstance(chars, list)
        and isinstance(starts, list)
        and isinstance(ends, list)
        and len(chars) == len(starts) == len(ends)
    )


def load_captions_from_elevenlabs_alignment(data: Dict[str, Any]) -> List[Tuple[str, float, float]]:
    """Load caption segments from ElevenLabs timing-only payload (dict).

    Expects data with "alignment" or "normalized_alignment" containing:
    - characters: list of single-char strings
    - character_start_times_seconds: list of floats
    - character_end_times_seconds: list of floats
    Optional top-level "text" is used for word display when length matches.

    Returns:
        List of (word, start_sec, end_sec).
    """
    align = data.get("alignment") or data.get("normalized_alignment")
    if not align:
        raise ValueError("Payload must contain 'alignment' or 'normalized_alignment'")
    chars = align.get("characters")
    starts = align.get("character_start_times_seconds")
    ends = align.get("character_end_times_seconds")
    if not chars or not starts or not ends:
        raise ValueError(
            "alignment must contain characters, character_start_times_seconds, character_end_times_seconds"
        )
    if len(chars) != len(starts) or len(starts) != len(ends):
        raise ValueError("alignment arrays must have the same length")
    # Normalize to list of strings and floats
    characters = [str(c) for c in chars]
    start_times = [float(s) for s in starts]
    end_times = [float(e) for e in ends]
    text = data.get("text")
    if text is not None:
        text = str(text)
    return alignment_to_word_segments(characters, start_times, end_times, text=text)


def load_captions(path_or_data: Union[str, Dict[str, Any]]) -> List[Tuple[str, float, float]]:
    """Load caption segments from a file path or in-memory dict (auto-detect format).

    Supports:
    - ElevenLabs timing-only payload: JSON object with "alignment" or "normalized_alignment"
      (characters, character_start_times_seconds, character_end_times_seconds). Optional "text".
    - Segment list: JSON array of {"text", "start", "end"} objects.

    Returns:
        List of (text, start_sec, end_sec).
    """
    if isinstance(path_or_data, dict):
        data = path_or_data
    else:
        p = Path(path_or_data)
        if not p.exists():
            raise FileNotFoundError(f"Captions file not found: {path_or_data}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

    if _is_elevenlabs_alignment_payload(data):
        return load_captions_from_elevenlabs_alignment(data)
    # Legacy: array of {text, start, end}
    return load_captions_from_json_data(data, path_or_data if isinstance(path_or_data, str) else None)


def load_captions_from_json_data(
    data: Any, path_for_errors: Optional[str] = None
) -> List[Tuple[str, float, float]]:
    """Load caption segments from a JSON array (list of {text, start, end})."""
    if not isinstance(data, list):
        raise ValueError(
            "Captions JSON must be an array of {text, start, end} objects"
            + (f": {path_for_errors}" if path_for_errors else "")
        )
    segments = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Captions item at index {i} must be an object")
        text = item.get("text")
        start = item.get("start")
        end = item.get("end")
        if text is None or start is None or end is None:
            raise ValueError(f"Captions item at index {i} must have 'text', 'start', 'end'")
        segments.append((str(text), float(start), float(end)))
    return segments


def extract_highlight_options(path_or_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Extract 'highlighted_words' and 'highlight_color' from captions JSON/dict (ElevenLabs-style).

    Returns subset dict for caption_options (empty if absent).
    """
    if isinstance(path_or_data, dict):
        data = path_or_data
    else:
        p = Path(path_or_data)
        if not p.exists():
            return {}
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    opts = {}
    if isinstance(data, dict):
        if "highlighted_words" in data and isinstance(data["highlighted_words"], list):
            # Normalize to lower for case-insensitive match
            opts["highlighted_words"] = [str(w).lower() for w in data["highlighted_words"]]
        if "highlight_color" in data:
            col = data["highlight_color"]
            if isinstance(col, (list, tuple)) and len(col) == 3:
                opts["highlight_color"] = tuple(int(c) for c in col)
    return opts


def _get_current_segment(
    t_sec: float,
    segments: List[Tuple[str, float, float]],
) -> Tuple[str, Optional[str], Optional[int], Optional[float], Optional[float]]:
    """Return (full_text, current_text, current_index, start_sec, end_sec) for t_sec.

    Only current_text used for drawing; timings enable pop progress calc.
    """
    if not segments:
        return "", None, None, None, None
    # Full line is all segments joined (kept for possible future use; not drawn)
    full_text = DEFAULT_CAPTION_OPTIONS["word_separator"].join(s[0] for s in segments)
    # Current word is the segment whose [start, end) contains t_sec
    for i, (text, start, end) in enumerate(segments):
        if start <= t_sec < end:
            return full_text, text, i, start, end
    # After last: keep last word (full duration for pop if needed)
    if t_sec >= segments[-1][2]:
        last_start, last_end = segments[-1][1], segments[-1][2]
        return full_text, segments[-1][0], len(segments) - 1, last_start, last_end
    # Before first: none
    return full_text, None, None, None, None


def _draw_text_with_outline(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    stroke_fill: Tuple[int, int, int],
    stroke_width: int,
    anchor: str = "lt",
) -> None:
    """Draw a single line of text with outline for readability on any background.
    anchor e.g. 'lt' = left-top, 'mt' = middle-top."""
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
        anchor=anchor,
    )


def overlay_captions_on_frame(
    frame_bgr: np.ndarray,
    t_sec: float,
    segments: List[Tuple[str, float, float]],
    width: int,
    height: int,
    options: Optional[Dict[str, Any]] = None,
) -> None:
    """Draw the current caption segment on a single BGR frame in place.

    Only current word drawn; optional pop-scale on appear (timing unchanged).

    Args:
        frame_bgr: OpenCV BGR frame (H, W, 3), modified in place.
        t_sec: Current time in seconds for this frame.
        segments: List of (text, start_sec, end_sec).
        width, height: Frame dimensions (used for layout).
        options: Optional overrides for DEFAULT_CAPTION_OPTIONS.
    """
    if not segments:
        return
    opts = {**DEFAULT_CAPTION_OPTIONS, **(options or {})}
    if not opts["show_emphasized"]:
        return
    stroke_fill = opts["stroke_color"]
    stroke_width = opts["stroke_width"]
    font = _get_font(opts["font_path"], opts["font_size_emphasized"])
    line_y_ratio = opts["line2_y_ratio"]

    # Get current segment + timings for pop progress
    _, current_text, _, seg_start, seg_end = _get_current_segment(t_sec, segments)
    if not current_text:
        return

    # Highlight check: if word in list (case-insensitive), use special color
    fill = opts["fill_color"]
    if opts["highlighted_words"] and current_text.lower() in opts["highlighted_words"]:
        fill = opts["highlight_color"]

    # Convert frame to PIL
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(frame_rgb)
    draw = ImageDraw.Draw(pil_img)

    def _text_width(draw_obj, text, font_obj):
        """Get text width in pixels; fallback for default font (no textbbox)."""
        try:
            bbox = draw_obj.textbbox((0, 0), text, font=font_obj)
            return bbox[2] - bbox[0]
        except (TypeError, AttributeError):
            return len(text) * (opts["font_size_emphasized"] // 2)

    # Single line: current word, centered at line_y_ratio
    line_y = int(height * line_y_ratio)
    tw = _text_width(draw, current_text, font)
    base_x = (width - tw) // 2

    # Pop animation: scale up during first pop_duration_ratio of word time (linear ease)
    # Keeps overall word timing/speed identical; just adds visual pop on appear
    if opts["pop_effect"] and seg_start is not None and seg_end is not None:
        dur = seg_end - seg_start
        if dur > 0:
            local_prog = max(0.0, min(1.0, (t_sec - seg_start) / dur))
            pop_ratio = opts["pop_duration_ratio"]
            if local_prog < pop_ratio:
                # Pop from pop_scale_start to 1.0
                pop_prog = local_prog / pop_ratio
                scale = opts["pop_scale_start"] + (1.0 - opts["pop_scale_start"]) * pop_prog
            else:
                scale = 1.0
        else:
            scale = 1.0
    else:
        scale = 1.0

    if scale == 1.0:
        # No pop: direct draw
        _draw_text_with_outline(
            draw, base_x, line_y, current_text, font, fill, stroke_fill, stroke_width, anchor="lt"
        )
    else:
        # Pop: render to temp img at full size, scale, paste centered
        temp = Image.new("RGBA", (int(tw * 1.2), int(opts["font_size_emphasized"] * 1.5)), (0, 0, 0, 0))
        tdraw = ImageDraw.Draw(temp)
        # Center in temp
        t_x = (temp.width - tw) // 2
        t_y = (temp.height - opts["font_size_emphasized"]) // 2
        _draw_text_with_outline(
            tdraw, t_x, t_y, current_text, font, fill, stroke_fill, stroke_width, anchor="lt"
        )
        # Scale temp
        new_size = (int(temp.width * scale), int(temp.height * scale))
        scaled = temp.resize(new_size, Image.LANCZOS)
        # Paste centered on main (adjust for scale shrink)
        paste_x = base_x - (new_size[0] - tw) // 2
        paste_y = line_y - (new_size[1] - opts["font_size_emphasized"]) // 2
        pil_img.paste(scaled, (paste_x, paste_y), scaled)

    # Write back to BGR frame
    frame_bgr[:] = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def overlay_captions_on_frames(
    frames: List[np.ndarray],
    segments: List[Tuple[str, float, float]],
    fps: float,
    width: int,
    height: int,
    options: Optional[Dict[str, Any]] = None,
    show_progress: bool = True,
) -> None:
    """Draw captions on each frame in place. Modifies frames list in place.

    Args:
        frames: List of BGR frames.
        segments: List of (text, start_sec, end_sec).
        fps: Frames per second.
        width, height: Frame dimensions.
        options: Optional caption style overrides.
        show_progress: Print progress every 60 frames.
    """
    if not segments:
        return
    total = len(frames)
    for frame_idx, frame in enumerate(frames):
        t_sec = frame_idx / fps
        overlay_captions_on_frame(frame, t_sec, segments, width, height, options)
        if show_progress and frame_idx % 60 == 0 and frame_idx > 0:
            print(f"Captions: {frame_idx}/{total} frames ({frame_idx * 100 // total}%)")


def load_captions_from_json(path: str) -> List[Tuple[str, float, float]]:
    """Load caption segments from a JSON file (auto-detects format).

    Supports both ElevenLabs timing payload and array of {text, start, end}.
    See load_captions() for supported formats.

    Returns:
        List of (text, start_sec, end_sec).
    """
    return load_captions(path)
