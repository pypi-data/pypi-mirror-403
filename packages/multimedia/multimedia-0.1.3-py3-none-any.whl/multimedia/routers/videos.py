"""Video listing and detail endpoints."""

import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional
import math

from ..database import list_videos, get_video_by_id, get_video_tags
from ..models import VideoBase, VideoDetail, VideoListResponse, SystemStatus, ScanStatus, Tag
from ..utils import format_relative_date, format_resolution, format_duration, format_file_size
from ..config import settings
from ..scanner import scan_directory, is_scanning, get_scan_status
from .stream import needs_transcoding

router = APIRouter(prefix="/api/videos", tags=["videos"])


def video_to_base(video: dict, tags: list[dict] = None) -> VideoBase:
    """Convert database video record to VideoBase model."""
    return VideoBase(
        id=video["id"],
        title=video["title"],
        thumbnail_url=f"/api/thumbnails/{video['id']}",
        duration=format_duration(video["duration_seconds"]),
        resolution=format_resolution(video["width"] or 0, video["height"] or 0),
        relative_date=format_relative_date(video["file_modified_at"]),
        file_size_human=format_file_size(video["file_size"]),
        tags=[Tag(**t) for t in (tags or [])],
    )


def video_to_detail(video: dict, tags: list[dict] = None) -> VideoDetail:
    """Convert database video record to VideoDetail model."""
    from datetime import datetime

    file_modified = video["file_modified_at"]
    if isinstance(file_modified, str):
        file_modified = datetime.fromisoformat(file_modified)

    video_path = Path(video["file_path"])
    is_transcoded = needs_transcoding(video_path, video.get("codec"))

    return VideoDetail(
        id=video["id"],
        title=video["title"],
        thumbnail_url=f"/api/thumbnails/{video['id']}",
        duration=format_duration(video["duration_seconds"]),
        resolution=format_resolution(video["width"] or 0, video["height"] or 0),
        relative_date=format_relative_date(video["file_modified_at"]),
        file_size_human=format_file_size(video["file_size"]),
        file_path=video["file_path"],
        width=video["width"] or 0,
        height=video["height"] or 0,
        codec=video["codec"],
        fps=video["fps"],
        bitrate=video["bitrate"],
        file_size=video["file_size"],
        file_modified_at=file_modified,
        stream_url=f"/api/stream/{video['id']}",
        tags=[Tag(**t) for t in (tags or [])],
        is_transcoded=is_transcoded,
    )


@router.get("", response_model=VideoListResponse)
async def get_videos(
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    search: Optional[str] = None,
    sort: str = Query("date_desc", pattern="^(date_desc|date_asc|title_asc|title_desc)$"),
):
    """List videos with pagination and search."""
    videos, total = await list_videos(
        page=page,
        per_page=per_page,
        search=search,
        sort=sort,
    )

    # Fetch tags for all videos concurrently
    video_tags = await asyncio.gather(*[get_video_tags(v["id"]) for v in videos])

    return VideoListResponse(
        videos=[video_to_base(v, tags) for v, tags in zip(videos, video_tags)],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=math.ceil(total / per_page) if total > 0 else 1,
    )


@router.get("/{video_id}", response_model=VideoDetail)
async def get_video(video_id: int):
    """Get a single video by ID."""
    video = await get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    tags = await get_video_tags(video_id)
    return video_to_detail(video, tags)


@router.post("/rescan")
async def rescan_videos(background_tasks: BackgroundTasks):
    """Trigger a rescan of the multimedia directory."""
    if is_scanning():
        return {"status": "already_scanning"}

    background_tasks.add_task(scan_directory)
    return {"status": "scan_started"}


@router.get("/status/info", response_model=SystemStatus)
async def get_status():
    """Get system status including scan progress."""
    videos, total = await list_videos(page=1, per_page=1)
    scan_status = get_scan_status()
    return SystemStatus(
        total_videos=total,
        multimedia_dir=str(settings.multimedia_dir),
        database_path=str(settings.database_path),
        scan=ScanStatus(**scan_status),
    )
