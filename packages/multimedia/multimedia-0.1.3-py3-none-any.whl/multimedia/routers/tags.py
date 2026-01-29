"""Tag management endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import math

from ..database import (
    get_all_tags,
    get_video_tags,
    add_tag_to_video,
    remove_tag_from_video,
    delete_unused_tags,
    list_videos_by_tag,
    list_untagged_videos,
    count_untagged_videos,
    get_tag_by_id,
    get_video_by_id,
)
from ..models import (
    Tag,
    TagWithCount,
    TagListResponse,
    AddTagRequest,
    VideoBase,
    VideoListResponse,
    VideoListByTagResponse,
)
from ..utils import format_relative_date, format_resolution, format_duration, format_file_size

router = APIRouter(prefix="/api/tags", tags=["tags"])


def video_to_base(video: dict) -> VideoBase:
    """Convert database video record to VideoBase model."""
    return VideoBase(
        id=video["id"],
        title=video["title"],
        thumbnail_url=f"/api/thumbnails/{video['id']}",
        duration=format_duration(video["duration_seconds"]),
        resolution=format_resolution(video["width"] or 0, video["height"] or 0),
        relative_date=format_relative_date(video["file_modified_at"]),
        file_size_human=format_file_size(video["file_size"]),
    )


@router.get("", response_model=TagListResponse)
async def list_tags():
    """Get all tags with video counts."""
    tags = await get_all_tags()
    return TagListResponse(
        tags=[TagWithCount(**tag) for tag in tags]
    )


@router.get("/untagged/count")
async def get_untagged_count():
    """Get count of videos without tags."""
    count = await count_untagged_videos()
    return {"count": count}


@router.get("/untagged/videos", response_model=VideoListResponse)
async def get_untagged_videos(
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    search: Optional[str] = None,
    sort: str = Query("date_desc", pattern="^(date_desc|date_asc|title_asc|title_desc)$"),
):
    """Get videos without any tags."""
    videos, total = await list_untagged_videos(
        page=page,
        per_page=per_page,
        search=search,
        sort=sort,
    )

    return VideoListResponse(
        videos=[video_to_base(v) for v in videos],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=math.ceil(total / per_page) if total > 0 else 1,
    )


@router.get("/{tag_id}/videos", response_model=VideoListByTagResponse)
async def get_videos_by_tag(
    tag_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    search: Optional[str] = None,
    sort: str = Query("date_desc", pattern="^(date_desc|date_asc|title_asc|title_desc)$"),
):
    """Get videos with a specific tag."""
    tag = await get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    videos, total = await list_videos_by_tag(
        tag_id=tag_id,
        page=page,
        per_page=per_page,
        search=search,
        sort=sort,
    )

    return VideoListByTagResponse(
        videos=[video_to_base(v) for v in videos],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=math.ceil(total / per_page) if total > 0 else 1,
        tag=Tag(id=tag["id"], name=tag["name"]),
    )


@router.get("/video/{video_id}", response_model=list[Tag])
async def get_tags_for_video(video_id: int):
    """Get all tags for a specific video."""
    video = await get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    tags = await get_video_tags(video_id)
    return [Tag(**tag) for tag in tags]


@router.post("/video/{video_id}", response_model=Tag)
async def add_tag(video_id: int, request: AddTagRequest):
    """Add a tag to a video."""
    video = await get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Tag name cannot be empty")

    tag = await add_tag_to_video(video_id, request.name)
    return Tag(**tag)


@router.delete("/video/{video_id}/{tag_id}")
async def remove_tag(video_id: int, tag_id: int):
    """Remove a tag from a video."""
    video = await get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    await remove_tag_from_video(video_id, tag_id)
    # Clean up unused tags
    await delete_unused_tags()
    return {"status": "ok"}
