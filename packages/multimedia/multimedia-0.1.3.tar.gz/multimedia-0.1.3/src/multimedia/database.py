"""SQLite database operations for caching video metadata."""

import aiosqlite
from typing import Optional
from datetime import datetime

from .config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_checksum TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    title TEXT NOT NULL,
    duration_seconds REAL,
    width INTEGER,
    height INTEGER,
    codec TEXT,
    bitrate INTEGER,
    fps REAL,
    thumbnail_path TEXT,
    file_modified_at DATETIME NOT NULL,
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_videos_checksum ON videos(file_checksum);
CREATE INDEX IF NOT EXISTS idx_videos_title ON videos(title);
CREATE INDEX IF NOT EXISTS idx_videos_file_modified ON videos(file_modified_at DESC);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

CREATE TABLE IF NOT EXISTS video_tags (
    video_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (video_id, tag_id),
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_video_tags_video ON video_tags(video_id);
CREATE INDEX IF NOT EXISTS idx_video_tags_tag ON video_tags(tag_id);

CREATE TABLE IF NOT EXISTS thumbnails (
    video_id INTEGER PRIMARY KEY,
    image_data BLOB NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);
"""


def _get_db_path() -> str:
    """Get database path as string."""
    return str(settings.database_path)


async def init_database() -> None:
    """Initialize the database schema."""
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def get_video_by_path(file_path: str) -> Optional[dict]:
    """Get a video record by file path."""
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM videos WHERE file_path = ?",
            (file_path,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_video_by_id(video_id: int) -> Optional[dict]:
    """Get a video record by ID."""
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM videos WHERE id = ?",
            (video_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def upsert_video(
    file_path: str,
    file_checksum: str,
    file_size: int,
    title: str,
    file_modified_at: datetime,
    duration_seconds: Optional[float] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    codec: Optional[str] = None,
    bitrate: Optional[int] = None,
    fps: Optional[float] = None,
) -> int:
    """Insert or update a video record. Returns the video ID."""
    async with aiosqlite.connect(_get_db_path()) as db:
        # Check if video already exists
        cursor = await db.execute(
            "SELECT id FROM videos WHERE file_path = ?",
            (file_path,)
        )
        existing = await cursor.fetchone()

        if existing:
            # Update existing video
            await db.execute(
                """
                UPDATE videos SET
                    file_checksum = ?,
                    file_size = ?,
                    title = ?,
                    file_modified_at = ?,
                    duration_seconds = ?,
                    width = ?,
                    height = ?,
                    codec = ?,
                    bitrate = ?,
                    fps = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE file_path = ?
                """,
                (
                    file_checksum, file_size, title, file_modified_at.isoformat(),
                    duration_seconds, width, height, codec, bitrate, fps,
                    file_path
                )
            )
            await db.commit()
            return existing[0]
        else:
            # Insert new video
            cursor = await db.execute(
                """
                INSERT INTO videos (
                    file_path, file_checksum, file_size, title, file_modified_at,
                    duration_seconds, width, height, codec, bitrate, fps
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_path, file_checksum, file_size, title, file_modified_at.isoformat(),
                    duration_seconds, width, height, codec, bitrate, fps
                )
            )
            await db.commit()
            return cursor.lastrowid


async def delete_video(file_path: str) -> None:
    """Delete a video record by file path."""
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute("DELETE FROM videos WHERE file_path = ?", (file_path,))
        await db.commit()


async def get_all_video_paths() -> set[str]:
    """Get all indexed video file paths."""
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT file_path FROM videos")
        rows = await cursor.fetchall()
        return {row["file_path"] for row in rows}


async def list_videos(
    page: int = 1,
    per_page: int = 24,
    search: Optional[str] = None,
    sort: str = "date_desc"
) -> tuple[list[dict], int]:
    """List videos with pagination and search. Returns (videos, total_count)."""
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row

        # Build query
        where_clause = ""
        params: list = []

        if search:
            where_clause = "WHERE title LIKE ?"
            params.append(f"%{search}%")

        # Sort order
        order_map = {
            "date_desc": "file_modified_at DESC",
            "date_asc": "file_modified_at ASC",
            "title_asc": "title ASC",
            "title_desc": "title DESC",
        }
        order_by = order_map.get(sort, "file_modified_at DESC")

        # Get total count
        count_cursor = await db.execute(
            f"SELECT COUNT(*) as count FROM videos {where_clause}",
            params
        )
        count_row = await count_cursor.fetchone()
        total = count_row["count"]

        # Get paginated results
        offset = (page - 1) * per_page
        cursor = await db.execute(
            f"""
            SELECT * FROM videos
            {where_clause}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset]
        )
        rows = await cursor.fetchall()
        videos = [dict(row) for row in rows]

        return videos, total


# Tag operations

async def get_or_create_tag(name: str) -> int:
    """Get or create a tag by name. Returns the tag ID."""
    name = name.strip().lower()
    async with aiosqlite.connect(_get_db_path()) as db:
        # Try to get existing tag
        cursor = await db.execute("SELECT id FROM tags WHERE name = ?", (name,))
        row = await cursor.fetchone()
        if row:
            return row[0]

        # Create new tag
        cursor = await db.execute("INSERT INTO tags (name) VALUES (?)", (name,))
        await db.commit()
        return cursor.lastrowid


async def get_all_tags() -> list[dict]:
    """Get all tags with video counts."""
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT t.id, t.name, COUNT(vt.video_id) as video_count
            FROM tags t
            LEFT JOIN video_tags vt ON t.id = vt.tag_id
            GROUP BY t.id
            ORDER BY t.name ASC
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_video_tags(video_id: int) -> list[dict]:
    """Get all tags for a video."""
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT t.id, t.name
            FROM tags t
            JOIN video_tags vt ON t.id = vt.tag_id
            WHERE vt.video_id = ?
            ORDER BY t.name ASC
        """, (video_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def add_tag_to_video(video_id: int, tag_name: str) -> dict:
    """Add a tag to a video. Creates the tag if it doesn't exist."""
    tag_id = await get_or_create_tag(tag_name)
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute(
            "INSERT OR IGNORE INTO video_tags (video_id, tag_id) VALUES (?, ?)",
            (video_id, tag_id)
        )
        await db.commit()
    return {"id": tag_id, "name": tag_name.strip().lower()}


async def remove_tag_from_video(video_id: int, tag_id: int) -> None:
    """Remove a tag from a video."""
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute(
            "DELETE FROM video_tags WHERE video_id = ? AND tag_id = ?",
            (video_id, tag_id)
        )
        await db.commit()


async def delete_unused_tags() -> int:
    """Delete tags that aren't associated with any videos. Returns count deleted."""
    async with aiosqlite.connect(_get_db_path()) as db:
        cursor = await db.execute("""
            DELETE FROM tags
            WHERE id NOT IN (SELECT DISTINCT tag_id FROM video_tags)
        """)
        await db.commit()
        return cursor.rowcount


async def list_videos_by_tag(
    tag_id: int,
    page: int = 1,
    per_page: int = 24,
    search: Optional[str] = None,
    sort: str = "date_desc"
) -> tuple[list[dict], int]:
    """List videos with a specific tag. Returns (videos, total_count)."""
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row

        # Build where clause
        where_parts = ["vt.tag_id = ?"]
        params: list = [tag_id]

        if search:
            where_parts.append("v.title LIKE ?")
            params.append(f"%{search}%")

        where_clause = " AND ".join(where_parts)

        # Sort order
        order_map = {
            "date_desc": "v.file_modified_at DESC",
            "date_asc": "v.file_modified_at ASC",
            "title_asc": "v.title ASC",
            "title_desc": "v.title DESC",
        }
        order_by = order_map.get(sort, "v.file_modified_at DESC")

        # Get total count
        count_cursor = await db.execute(
            f"""
            SELECT COUNT(*) as count
            FROM videos v
            JOIN video_tags vt ON v.id = vt.video_id
            WHERE {where_clause}
            """,
            params
        )
        count_row = await count_cursor.fetchone()
        total = count_row["count"]

        # Get paginated results
        offset = (page - 1) * per_page
        cursor = await db.execute(
            f"""
            SELECT v.*
            FROM videos v
            JOIN video_tags vt ON v.id = vt.video_id
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset]
        )
        rows = await cursor.fetchall()
        videos = [dict(row) for row in rows]

        return videos, total


async def list_untagged_videos(
    page: int = 1,
    per_page: int = 24,
    search: Optional[str] = None,
    sort: str = "date_desc"
) -> tuple[list[dict], int]:
    """List videos without any tags. Returns (videos, total_count)."""
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row

        # Build where clause
        where_parts = ["NOT EXISTS (SELECT 1 FROM video_tags vt WHERE vt.video_id = v.id)"]
        params: list = []

        if search:
            where_parts.append("v.title LIKE ?")
            params.append(f"%{search}%")

        where_clause = " AND ".join(where_parts)

        # Sort order
        order_map = {
            "date_desc": "v.file_modified_at DESC",
            "date_asc": "v.file_modified_at ASC",
            "title_asc": "v.title ASC",
            "title_desc": "v.title DESC",
        }
        order_by = order_map.get(sort, "v.file_modified_at DESC")

        # Get total count
        count_cursor = await db.execute(
            f"""
            SELECT COUNT(*) as count
            FROM videos v
            WHERE {where_clause}
            """,
            params
        )
        count_row = await count_cursor.fetchone()
        total = count_row["count"]

        # Get paginated results
        offset = (page - 1) * per_page
        cursor = await db.execute(
            f"""
            SELECT v.*
            FROM videos v
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset]
        )
        rows = await cursor.fetchall()
        videos = [dict(row) for row in rows]

        return videos, total


async def count_untagged_videos() -> int:
    """Get count of videos without any tags."""
    async with aiosqlite.connect(_get_db_path()) as db:
        cursor = await db.execute(
            """
            SELECT COUNT(*) as count
            FROM videos v
            WHERE NOT EXISTS (SELECT 1 FROM video_tags vt WHERE vt.video_id = v.id)
            """
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_tag_by_id(tag_id: int) -> Optional[dict]:
    """Get a tag by ID."""
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


# Thumbnail operations

async def save_thumbnail(video_id: int, image_data: bytes) -> None:
    """Save or update a thumbnail for a video."""
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute(
            """
            INSERT INTO thumbnails (video_id, image_data)
            VALUES (?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                image_data = excluded.image_data,
                created_at = CURRENT_TIMESTAMP
            """,
            (video_id, image_data)
        )
        await db.commit()


async def get_thumbnail(video_id: int) -> Optional[bytes]:
    """Get thumbnail image data for a video."""
    async with aiosqlite.connect(_get_db_path()) as db:
        cursor = await db.execute(
            "SELECT image_data FROM thumbnails WHERE video_id = ?",
            (video_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def delete_thumbnail(video_id: int) -> None:
    """Delete a thumbnail for a video."""
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute("DELETE FROM thumbnails WHERE video_id = ?", (video_id,))
        await db.commit()
