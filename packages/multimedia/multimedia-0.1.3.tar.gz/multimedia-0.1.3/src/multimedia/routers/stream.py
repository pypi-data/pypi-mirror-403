"""Video streaming endpoint with HTTP 206 range request support and HLS transcoding."""

import subprocess
import hashlib
import tempfile
import threading
import time
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse, RedirectResponse

from ..database import get_video_by_id
from ..config import settings

router = APIRouter(prefix="/api/stream", tags=["stream"])

# Cache directory for transcoded videos and HLS segments
TRANSCODE_CACHE_DIR = Path(tempfile.gettempdir()) / "multimedia_transcode_cache"
TRANSCODE_CACHE_DIR.mkdir(exist_ok=True)

# Track active HLS transcoding jobs
_active_hls_jobs: dict[str, subprocess.Popen] = {}
_hls_jobs_lock = threading.Lock()

CONTENT_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".m4v": "video/x-m4v",
    ".wmv": "video/x-ms-wmv",
    ".flv": "video/x-flv",
    ".mpeg": "video/mpeg",
    ".mpg": "video/mpeg",
}

# Formats that browsers can play natively (with common codecs)
BROWSER_NATIVE_EXTENSIONS = {".mp4", ".webm", ".m4v", ".mov"}

# Codecs that browsers support natively
BROWSER_NATIVE_CODECS = {"h264", "avc1", "hevc", "h265", "vp8", "vp9", "av1"}


def get_content_type(path: Path) -> str:
    """Get the content type for a video file."""
    return CONTENT_TYPES.get(path.suffix.lower(), "video/mp4")


def needs_transcoding(video_path: Path, codec: Optional[str]) -> bool:
    """Check if a video needs transcoding for browser playback."""
    ext = video_path.suffix.lower()

    # Always transcode these formats
    if ext in {".flv", ".avi", ".wmv", ".mpeg", ".mpg"}:
        return True

    # MKV might work but is unreliable across browsers
    if ext == ".mkv":
        return True

    # Check codec if available
    if codec:
        codec_lower = codec.lower()
        # If codec is not browser-native, transcode
        if not any(native in codec_lower for native in BROWSER_NATIVE_CODECS):
            return True

    return False


def get_cache_path(video_path: Path) -> Path:
    """Get the cache file path for a transcoded video."""
    # Create a hash of the source path and modification time for cache key
    stat = video_path.stat()
    cache_key = f"{video_path}:{stat.st_mtime}:{stat.st_size}"
    hash_key = hashlib.md5(cache_key.encode()).hexdigest()
    return TRANSCODE_CACHE_DIR / f"{hash_key}.mp4"


def transcode_to_file(video_path: Path, output_path: Path) -> bool:
    """Transcode video to a file with iOS-compatible settings.

    Returns True if transcoding succeeded, False otherwise.
    """
    temp_output = output_path.with_suffix('.tmp.mp4')

    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-i", str(video_path),
        "-c:v", "libx264",
        "-profile:v", "baseline",  # Most compatible H.264 profile for iOS
        "-level", "3.1",           # Widely supported level
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",  # Move moov atom to beginning for streaming
        "-f", "mp4",
        str(temp_output)
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=600,  # 10 minute timeout
        )
        if result.returncode == 0 and temp_output.exists():
            temp_output.rename(output_path)
            return True
    except subprocess.TimeoutExpired:
        pass
    finally:
        # Clean up temp file if it exists
        if temp_output.exists():
            temp_output.unlink()

    return False


def is_transcoding_in_progress(cache_path: Path) -> bool:
    """Check if transcoding is currently in progress for this file."""
    temp_path = cache_path.with_suffix('.tmp.mp4')
    return temp_path.exists()


def get_hls_cache_dir(video_path: Path) -> Path:
    """Get the HLS cache directory for a video."""
    stat = video_path.stat()
    cache_key = f"{video_path}:{stat.st_mtime}:{stat.st_size}"
    hash_key = hashlib.md5(cache_key.encode()).hexdigest()
    hls_dir = TRANSCODE_CACHE_DIR / f"hls_{hash_key}"
    hls_dir.mkdir(exist_ok=True)
    return hls_dir


def check_ffmpeg_available() -> bool:
    """Check if ffmpeg is available in PATH."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


def get_hw_encoder() -> tuple[str, list[str]]:
    """Detect available hardware encoder.

    Returns (encoder_name, extra_args) tuple.
    """
    # Try VideoToolbox (macOS)
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "h264_videotoolbox" in result.stdout:
            return "h264_videotoolbox", ["-q:v", "65"]  # Quality scale for VT
    except:
        pass

    # Try NVENC (NVIDIA)
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "h264_nvenc" in result.stdout:
            return "h264_nvenc", ["-preset", "fast", "-cq", "23"]
    except:
        pass

    # Try VAAPI (Linux)
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "h264_vaapi" in result.stdout:
            return "h264_vaapi", ["-qp", "23"]
    except:
        pass

    # Fallback to software
    return "libx264", ["-preset", "ultrafast", "-tune", "zerolatency", "-crf", "23"]


# Cache the encoder detection result
_detected_encoder: tuple[str, list[str]] | None = None


def get_video_encoder() -> tuple[str, list[str]]:
    """Get the best available video encoder (cached)."""
    global _detected_encoder
    if _detected_encoder is None:
        _detected_encoder = get_hw_encoder()
        logger.info(f"Detected video encoder: {_detected_encoder[0]}")
    return _detected_encoder


def start_hls_transcode(video_path: Path, hls_dir: Path) -> subprocess.Popen | None:
    """Start HLS transcoding in background if not already running.

    Returns the process if started/running, None if already complete.
    """
    job_key = str(hls_dir)

    with _hls_jobs_lock:
        # Check if job already running
        if job_key in _active_hls_jobs:
            proc = _active_hls_jobs[job_key]
            if proc.poll() is None:  # Still running
                return proc
            else:
                del _active_hls_jobs[job_key]

        # Check if already fully transcoded
        playlist_path = hls_dir / "playlist.m3u8"
        if playlist_path.exists():
            content = playlist_path.read_text()
            if "#EXT-X-ENDLIST" in content:
                return None  # Already complete

        # Get the best available encoder (hardware if available)
        encoder, encoder_args = get_video_encoder()

        # Start new transcode job with optimized settings for fast start
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            # Video encoding
            "-c:v", encoder,
            "-pix_fmt", "yuv420p",  # Convert to 8-bit (required for 10-bit sources)
            *encoder_args,
            # Audio: AAC stereo
            "-c:a", "aac",
            "-ac", "2",
            "-b:a", "128k",
            # HLS output
            "-f", "hls",
            "-hls_time", "2",
            "-hls_list_size", "0",
            "-hls_segment_filename", str(hls_dir / "segment_%03d.ts"),
            "-start_number", "0",
            str(hls_dir / "playlist.m3u8")
        ]

        # Log the command for debugging
        log_file = hls_dir / "ffmpeg.log"
        logger.info(f"Starting HLS transcode: {' '.join(cmd)}")
        logger.info(f"Output directory: {hls_dir}")
        log_handle = open(log_file, "w")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=log_handle,
        )
        _active_hls_jobs[job_key] = proc
        logger.info(f"FFmpeg process started with PID: {proc.pid}")
        return proc


def wait_for_playlist(hls_dir: Path, proc: subprocess.Popen | None, timeout: float = 15.0) -> tuple[bool, str]:
    """Wait for the HLS playlist to be created with at least one segment.

    Returns (success, error_message).
    """
    playlist_path = hls_dir / "playlist.m3u8"
    log_file = hls_dir / "ffmpeg.log"
    start_time = time.time()

    # If no process, check if playlist already exists
    if proc is None:
        logger.info("No process provided, checking for existing playlist")
        if playlist_path.exists():
            return True, ""
        return False, "No transcoding process and no playlist"

    logger.info(f"Waiting for playlist at {playlist_path}")

    while time.time() - start_time < timeout:
        # Check if process died
        poll_result = proc.poll()
        if poll_result is not None:
            logger.warning(f"FFmpeg process ended with code: {poll_result}")
            # Process ended - check if it succeeded
            if playlist_path.exists():
                content = playlist_path.read_text()
                if ".ts" in content and "#EXTINF:" in content:
                    logger.info("Playlist ready after process ended")
                    return True, ""

            # Process failed - read error log
            error_msg = f"FFmpeg process ended with code {poll_result}"
            if log_file.exists():
                try:
                    log_content = log_file.read_text()
                    logger.error(f"FFmpeg log:\n{log_content}")
                    # Get last few lines of log
                    lines = log_content.strip().split('\n')
                    error_msg = '\n'.join(lines[-10:]) if lines else error_msg
                except Exception as e:
                    logger.error(f"Failed to read log: {e}")
            return False, error_msg

        if playlist_path.exists():
            try:
                content = playlist_path.read_text()
                # Check if playlist has at least one segment
                if ".ts" in content and "#EXTINF:" in content:
                    logger.info("Playlist ready with segments")
                    return True, ""
            except:
                pass  # File might be being written

        time.sleep(0.3)

    # Timeout - check what files exist
    files = list(hls_dir.glob("*"))
    logger.warning(f"Timeout. Files in {hls_dir}: {files}")
    if log_file.exists():
        logger.error(f"FFmpeg log:\n{log_file.read_text()}")

    return False, f"Timeout waiting for first segment. Files: {[f.name for f in files]}"


def serve_file_with_range(file_path: Path, range_header: Optional[str], content_type: str):
    """Serve a file with HTTP range request support."""
    file_size = file_path.stat().st_size

    if range_header:
        range_str = range_header.replace("bytes=", "")
        parts = range_str.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else min(start + settings.chunk_size - 1, file_size - 1)
        end = min(end, file_size - 1)

        def iter_file():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk_size = min(settings.chunk_size, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
        }

        return StreamingResponse(
            iter_file(),
            status_code=206,
            headers=headers,
            media_type=content_type,
        )

    def iter_full_file():
        with open(file_path, "rb") as f:
            while chunk := f.read(settings.chunk_size):
                yield chunk

    return StreamingResponse(
        iter_full_file(),
        media_type=content_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
        }
    )


@router.get("/{video_id}")
async def stream_video(
    video_id: int,
    range: Optional[str] = Header(None),
):
    """Stream a video file with range request support."""
    video = await get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = Path(video["file_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # Check if transcoding is needed - use HLS for iOS compatibility
    if needs_transcoding(video_path, video.get("codec")):
        # Redirect to HLS playlist
        return RedirectResponse(
            url=f"/api/stream/{video_id}/hls/playlist.m3u8",
            status_code=302
        )

    # Native playback with range support
    file_size = video_path.stat().st_size
    content_type = get_content_type(video_path)

    if range:
        range_str = range.replace("bytes=", "")
        parts = range_str.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else min(start + settings.chunk_size - 1, file_size - 1)

        end = min(end, file_size - 1)

        def iter_file():
            with open(video_path, "rb") as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk_size = min(settings.chunk_size, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
        }

        return StreamingResponse(
            iter_file(),
            status_code=206,
            headers=headers,
            media_type=content_type,
        )

    def iter_full_file():
        with open(video_path, "rb") as f:
            while chunk := f.read(settings.chunk_size):
                yield chunk

    return StreamingResponse(
        iter_full_file(),
        media_type=content_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
        }
    )


@router.get("/{video_id}/hls/progress")
async def get_hls_progress(video_id: int):
    """Get HLS transcoding progress for a video."""
    video = await get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = Path(video["file_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # Get video duration in seconds
    total_duration = video.get("duration_seconds", 0)
    if not total_duration:
        # Try to parse from duration string (HH:MM:SS)
        duration_str = video.get("duration", "")
        if duration_str:
            parts = duration_str.split(":")
            if len(parts) == 3:
                total_duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            elif len(parts) == 2:
                total_duration = int(parts[0]) * 60 + float(parts[1])

    hls_dir = get_hls_cache_dir(video_path)
    playlist_path = hls_dir / "playlist.m3u8"

    if not playlist_path.exists():
        return {
            "status": "pending",
            "transcoded_seconds": 0,
            "total_seconds": total_duration,
            "percent": 0,
            "is_complete": False,
        }

    # Parse playlist to get transcoded duration
    content = playlist_path.read_text()
    is_complete = "#EXT-X-ENDLIST" in content

    # Sum up segment durations from #EXTINF: lines
    transcoded_seconds = 0
    for line in content.split('\n'):
        if line.startswith('#EXTINF:'):
            try:
                duration = float(line.split(':')[1].split(',')[0])
                transcoded_seconds += duration
            except:
                pass

    percent = (transcoded_seconds / total_duration * 100) if total_duration > 0 else 0

    return {
        "status": "complete" if is_complete else "transcoding",
        "transcoded_seconds": round(transcoded_seconds, 1),
        "total_seconds": round(total_duration, 1),
        "percent": min(round(percent, 1), 100),
        "is_complete": is_complete,
    }


@router.get("/{video_id}/hls/playlist.m3u8")
async def get_hls_playlist(video_id: int):
    """Get HLS playlist for a video, starting transcoding if needed."""
    # Check ffmpeg is available
    if not check_ffmpeg_available():
        raise HTTPException(
            status_code=503,
            detail="FFmpeg is not available on this server"
        )

    video = await get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = Path(video["file_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    hls_dir = get_hls_cache_dir(video_path)

    # Check if playlist already exists and is complete
    playlist_path = hls_dir / "playlist.m3u8"
    if playlist_path.exists():
        content = playlist_path.read_text()
        if "#EXT-X-ENDLIST" in content and ".ts" in content:
            # Already complete, serve it
            content = re.sub(
                r'(segment_\d+\.ts)',
                rf'/api/stream/{video_id}/hls/\1',
                content
            )
            return PlainTextResponse(
                content=content,
                media_type="application/vnd.apple.mpegurl",
                headers={"Cache-Control": "max-age=3600"},
            )

    # Start transcoding if not already running
    proc = start_hls_transcode(video_path, hls_dir)

    # Wait for playlist to be ready
    success, error_msg = wait_for_playlist(hls_dir, proc, timeout=15.0)
    if not success:
        # Clean up failed attempt
        log_file = hls_dir / "ffmpeg.log"
        log_content = ""
        if log_file.exists():
            try:
                log_content = log_file.read_text()[-500:]  # Last 500 chars
            except:
                pass
        raise HTTPException(
            status_code=503,
            detail=f"Transcoding failed: {error_msg}. Log: {log_content}"
        )

    playlist_path = hls_dir / "playlist.m3u8"

    # Read and modify playlist to use our segment endpoint
    content = playlist_path.read_text()

    # Replace segment filenames with our API URLs
    content = re.sub(
        r'(segment_\d+\.ts)',
        rf'/api/stream/{video_id}/hls/\1',
        content
    )

    return PlainTextResponse(
        content=content,
        media_type="application/vnd.apple.mpegurl",
        headers={
            "Cache-Control": "no-cache",
        }
    )


@router.get("/{video_id}/hls/{segment}")
async def get_hls_segment(video_id: int, segment: str):
    """Get an HLS segment file."""
    # Validate segment filename
    if not segment.startswith("segment_") or not segment.endswith(".ts"):
        raise HTTPException(status_code=400, detail="Invalid segment name")

    video = await get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = Path(video["file_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    hls_dir = get_hls_cache_dir(video_path)
    segment_path = hls_dir / segment

    # Wait a bit for segment to be created if transcoding is in progress
    for _ in range(50):  # Wait up to 5 seconds
        if segment_path.exists():
            break
        time.sleep(0.1)

    if not segment_path.exists():
        raise HTTPException(status_code=404, detail="Segment not found")

    return FileResponse(
        segment_path,
        media_type="video/mp2t",
        headers={
            "Cache-Control": "max-age=3600",
        }
    )
