"""Configuration settings for multimedia service."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    multimedia_dir: Path = Path(os.getenv("MULTIMEDIA_DIR", ".")).resolve()
    host: str = "0.0.0.0"
    port: int = 8028

    # Authentication
    passphrase: Optional[str] = None

    # Thumbnail settings
    thumbnail_width: int = 320
    thumbnail_seek_seconds: float = 10.0

    # Supported video formats
    supported_formats: tuple[str, ...] = (
        ".mp4", ".mkv", ".avi", ".mov", ".webm",
        ".m4v", ".wmv", ".flv", ".mpeg", ".mpg"
    )

    # Streaming settings
    chunk_size: int = 1024 * 1024  # 1MB

    # Pagination
    default_page_size: int = 24
    max_page_size: int = 100

    @property
    def database_path(self) -> Path:
        """Path to the SQLite database file."""
        return self.multimedia_dir / ".multimedia.db"

    class Config:
        env_prefix = "MULTIMEDIA_"


settings = Settings()
