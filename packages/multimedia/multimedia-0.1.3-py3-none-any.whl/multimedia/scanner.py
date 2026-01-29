"""Video file scanner for indexing media files."""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from .config import settings
from .database import (
    get_video_by_path,
    upsert_video,
    delete_video,
    get_all_video_paths,
    save_thumbnail,
)
from .utils import calculate_file_checksum
from .video_processor import extract_metadata, generate_thumbnail


@dataclass
class ScanProgress:
    """Tracks the progress of a directory scan."""

    scanning: bool = False
    total_files: int = 0
    processed_files: int = 0
    current_file: Optional[str] = None
    new_files: int = 0
    skipped_files: int = 0
    error_count: int = 0
    last_scanned_at: Optional[datetime] = None


_scan_progress = ScanProgress()


def get_scan_status() -> dict:
    """Get the current scan status."""
    return {
        "scanning": _scan_progress.scanning,
        "total_files": _scan_progress.total_files,
        "processed_files": _scan_progress.processed_files,
        "current_file": _scan_progress.current_file,
        "new_files": _scan_progress.new_files,
        "skipped_files": _scan_progress.skipped_files,
        "error_count": _scan_progress.error_count,
        "remaining_files": max(0, _scan_progress.total_files - _scan_progress.processed_files),
        "last_scanned_at": _scan_progress.last_scanned_at.isoformat() if _scan_progress.last_scanned_at else None,
    }


def is_scanning() -> bool:
    """Check if a scan is currently in progress."""
    return _scan_progress.scanning


def _find_video_files_sync() -> list[Path]:
    """Synchronously find all video files (runs in thread pool)."""
    files = []
    seen = set()
    for ext in settings.supported_formats:
        for path in settings.multimedia_dir.rglob(f"*{ext}"):
            if path.is_file() and not path.name.startswith(".") and path not in seen:
                files.append(path)
                seen.add(path)
        for path in settings.multimedia_dir.rglob(f"*{ext.upper()}"):
            if path.is_file() and not path.name.startswith(".") and path not in seen:
                files.append(path)
                seen.add(path)
    return files


def _process_video_sync(video_path: Path) -> tuple[bool, Optional[dict], Optional[str]]:
    """Synchronously process video metadata and thumbnail (runs in thread pool).

    Returns (is_new, metadata_dict, error_message).
    """
    try:
        # Resolve to absolute path for consistent storage
        resolved_path = video_path.resolve()
        file_stat = resolved_path.stat()
        file_checksum = calculate_file_checksum(resolved_path)
        file_size = file_stat.st_size
        file_modified = datetime.fromtimestamp(file_stat.st_mtime)

        metadata = extract_metadata(resolved_path)

        return True, {
            "file_path": str(resolved_path),
            "file_checksum": file_checksum,
            "file_size": file_size,
            "file_modified": file_modified,
            "title": metadata.title,
            "duration_seconds": metadata.duration_seconds,
            "width": metadata.width,
            "height": metadata.height,
            "codec": metadata.codec,
            "bitrate": metadata.bitrate,
            "fps": metadata.fps,
        }, None
    except Exception as e:
        return False, None, str(e)


async def process_video_file(video_path: Path) -> bool:
    """Process a single video file.

    Returns True if the file was processed (new or updated), False if skipped.
    """
    # Resolve to absolute path for consistent lookups
    resolved_path = video_path.resolve()
    file_path_str = str(resolved_path)

    # Check if already indexed
    existing = await get_video_by_path(file_path_str)

    if existing:
        # Quick check: if file size and mtime match, skip without reading file
        file_stat = await asyncio.to_thread(resolved_path.stat)
        file_size = file_stat.st_size
        file_mtime = datetime.fromtimestamp(file_stat.st_mtime)

        stored_mtime = existing["file_modified_at"]
        if isinstance(stored_mtime, str):
            stored_mtime = datetime.fromisoformat(stored_mtime)

        # If size and mtime match, skip entirely (no checksum needed)
        if existing["file_size"] == file_size and abs((stored_mtime - file_mtime).total_seconds()) < 1:
            return False

    # File is new or modified - calculate checksum for verification
    file_checksum = await asyncio.to_thread(calculate_file_checksum, resolved_path)

    if existing and existing["file_checksum"] == file_checksum:
        return False

    # Process video in thread pool
    success, data, error = await asyncio.to_thread(_process_video_sync, resolved_path)

    if not success or not data:
        if error:
            print(f"Error extracting metadata from {resolved_path}: {error}")
        return False

    video_id = await upsert_video(
        file_path=data["file_path"],
        file_checksum=data["file_checksum"],
        file_size=data["file_size"],
        title=data["title"],
        file_modified_at=data["file_modified"],
        duration_seconds=data["duration_seconds"],
        width=data["width"],
        height=data["height"],
        codec=data["codec"],
        bitrate=data["bitrate"],
        fps=data["fps"],
    )

    # Generate thumbnail in thread pool and save to DB
    seek = min(settings.thumbnail_seek_seconds, data["duration_seconds"] / 2)

    thumbnail_data = await asyncio.to_thread(
        generate_thumbnail, resolved_path, settings.thumbnail_width, seek
    )

    if thumbnail_data:
        await save_thumbnail(video_id, thumbnail_data)

    return True


async def cleanup_deleted_files(found_paths: set[str]) -> int:
    """Remove database entries for files that no longer exist.

    Returns count of deleted entries.
    Thumbnails are automatically deleted via CASCADE constraint.
    """
    indexed_paths = await get_all_video_paths()
    deleted_count = 0

    for indexed_path in indexed_paths:
        if indexed_path not in found_paths:
            await delete_video(indexed_path)
            deleted_count += 1

    return deleted_count


async def scan_directory() -> dict:
    """Scan the multimedia directory for video files.

    Returns a summary of the scan results.
    """
    global _scan_progress

    if _scan_progress.scanning:
        return {"status": "already_scanning"}

    # Reset progress
    _scan_progress = ScanProgress(scanning=True)

    try:
        # Find all files in thread pool to avoid blocking
        _scan_progress.current_file = "Discovering files..."
        video_files = await asyncio.to_thread(_find_video_files_sync)
        _scan_progress.total_files = len(video_files)

        found_paths: set[str] = set()

        for video_path in video_files:
            # Use resolved path to match database storage
            found_paths.add(str(video_path.resolve()))
            _scan_progress.current_file = video_path.name

            try:
                if await process_video_file(video_path):
                    _scan_progress.new_files += 1
                else:
                    _scan_progress.skipped_files += 1
            except Exception as e:
                print(f"Error processing {video_path}: {e}")
                _scan_progress.error_count += 1

            _scan_progress.processed_files += 1

        deleted_count = await cleanup_deleted_files(found_paths)

        return {
            "status": "completed",
            "found": len(found_paths),
            "processed": _scan_progress.new_files,
            "skipped": _scan_progress.skipped_files,
            "deleted": deleted_count,
            "errors": _scan_progress.error_count,
        }
    finally:
        _scan_progress.scanning = False
        _scan_progress.current_file = None
        _scan_progress.last_scanned_at = datetime.now()
