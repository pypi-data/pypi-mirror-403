"""Pydantic models for API responses."""

from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class Tag(BaseModel):
    """Tag information."""

    id: int
    name: str


class VideoBase(BaseModel):
    """Base video information for list view."""

    id: int
    title: str
    thumbnail_url: str
    duration: str
    resolution: str
    relative_date: str
    file_size_human: str
    tags: list[Tag] = []


class TagWithCount(Tag):
    """Tag with video count."""

    video_count: int


class VideoDetail(VideoBase):
    """Detailed video information for single video view."""

    file_path: str
    width: int
    height: int
    codec: Optional[str]
    fps: Optional[float]
    bitrate: Optional[int]
    file_size: int
    file_modified_at: datetime
    stream_url: str
    is_transcoded: bool = False


class VideoListResponse(BaseModel):
    """Response for video list endpoint."""

    videos: list[VideoBase]
    total: int
    page: int
    per_page: int
    total_pages: int


class ScanStatus(BaseModel):
    """Scan progress information."""

    scanning: bool
    total_files: int
    processed_files: int
    remaining_files: int
    current_file: Optional[str]
    new_files: int
    skipped_files: int
    error_count: int
    last_scanned_at: Optional[datetime]


class SystemStatus(BaseModel):
    """System status information."""

    total_videos: int
    multimedia_dir: str
    database_path: str
    scan: ScanStatus


class TagListResponse(BaseModel):
    """Response for tag list endpoint."""

    tags: list[TagWithCount]


class AddTagRequest(BaseModel):
    """Request to add a tag to a video."""

    name: str


class VideoListByTagResponse(VideoListResponse):
    """Response for video list filtered by tag."""

    tag: Tag
