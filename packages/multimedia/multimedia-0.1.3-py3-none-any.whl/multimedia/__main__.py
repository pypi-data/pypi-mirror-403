"""Entry point for running multimedia as a module or CLI."""

import uvicorn
from .config import settings


def main():
    """Run the multimedia server."""
    print(f"Starting Multimedia server...")
    print(f"Media directory: {settings.multimedia_dir}")
    print(f"Database: {settings.database_path}")
    print(f"Listening on http://{settings.host}:{settings.port}")

    uvicorn.run(
        "multimedia.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
