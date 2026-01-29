"""Video processing using FFmpeg for thumbnails and metadata extraction."""

import subprocess
import shutil
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .config import settings


_ffmpeg_available: Optional[bool] = None
_ffprobe_available: Optional[bool] = None


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available in PATH."""
    global _ffmpeg_available
    if _ffmpeg_available is None:
        _ffmpeg_available = shutil.which("ffmpeg") is not None
    return _ffmpeg_available


def check_ffprobe() -> bool:
    """Check if ffprobe is available in PATH."""
    global _ffprobe_available
    if _ffprobe_available is None:
        _ffprobe_available = shutil.which("ffprobe") is not None
    return _ffprobe_available


def check_dependencies() -> tuple[bool, str]:
    """Check if required dependencies are available.

    Returns (success, message).
    """
    missing = []
    if not check_ffprobe():
        missing.append("ffprobe")
    if not check_ffmpeg():
        missing.append("ffmpeg")

    if missing:
        return False, (
            f"Missing required dependencies: {', '.join(missing)}\n"
            "Please install FFmpeg: https://ffmpeg.org/download.html\n"
            "  - macOS: brew install ffmpeg\n"
            "  - Ubuntu/Debian: apt install ffmpeg\n"
            "  - Windows: download from ffmpeg.org or use chocolatey"
        )
    return True, "All dependencies available"


@dataclass
class VideoMetadata:
    """Video metadata extracted from ffprobe."""

    title: str
    duration_seconds: float
    width: int
    height: int
    codec: Optional[str]
    bitrate: Optional[int]
    fps: Optional[float]


def extract_metadata(video_path: Path) -> VideoMetadata:
    """Extract video metadata using ffprobe."""
    if not check_ffprobe():
        raise RuntimeError(
            "ffprobe not found. Please install FFmpeg: https://ffmpeg.org/download.html"
        )

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {video_path}: {result.stderr}")

    data = json.loads(result.stdout)

    video_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
        {}
    )

    format_info = data.get("format", {})
    tags = format_info.get("tags", {})

    title = (
        tags.get("title")
        or tags.get("TITLE")
        or video_path.stem
    )

    fps = None
    frame_rate = video_stream.get("r_frame_rate", "")
    if frame_rate and "/" in frame_rate:
        try:
            num, denom = frame_rate.split("/")
            fps = float(num) / float(denom) if float(denom) != 0 else None
        except (ValueError, ZeroDivisionError):
            pass

    return VideoMetadata(
        title=title,
        duration_seconds=float(format_info.get("duration", 0)),
        width=int(video_stream.get("width", 0)),
        height=int(video_stream.get("height", 0)),
        codec=video_stream.get("codec_name"),
        bitrate=int(format_info.get("bit_rate", 0)) if format_info.get("bit_rate") else None,
        fps=fps,
    )


def generate_thumbnail(
    video_path: Path,
    width: int = 320,
    seek_seconds: float = 10.0
) -> Optional[bytes]:
    """Generate thumbnail at specified timestamp.

    Returns JPEG image bytes on success, None on failure.
    """
    if not check_ffmpeg():
        return None

    cmd = [
        "ffmpeg",
        "-ss", str(seek_seconds),
        "-i", str(video_path),
        "-vframes", "1",
        "-vf", f"scale={width}:-1",
        "-q:v", "2",
        "-f", "mjpeg",
        "-"
    ]

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0 and result.stdout:
        return result.stdout
    return None


async def process_video(video_path: Path) -> Optional[VideoMetadata]:
    """Process a video file and extract metadata.

    Returns metadata on success, None on failure.
    """
    try:
        return extract_metadata(video_path)
    except Exception as e:
        print(f"Error processing video {video_path}: {e}")
        return None
