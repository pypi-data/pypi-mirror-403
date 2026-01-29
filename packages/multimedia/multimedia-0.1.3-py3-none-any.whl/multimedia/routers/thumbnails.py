"""Thumbnail serving endpoint."""

import hashlib

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from ..database import get_video_by_id, get_thumbnail

router = APIRouter(prefix="/api/thumbnails", tags=["thumbnails"])


@router.get("/{video_id}")
async def serve_thumbnail(video_id: int, request: Request):
    """Get the thumbnail for a video."""
    video = await get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    thumbnail_data = await get_thumbnail(video_id)

    if not thumbnail_data:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    # Generate ETag from thumbnail content hash
    etag = f'"{hashlib.md5(thumbnail_data).hexdigest()}"'

    # Check If-None-Match for conditional request
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match == etag:
        return Response(status_code=304, headers={"ETag": etag})

    return Response(
        content=thumbnail_data,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "ETag": etag,
        }
    )
