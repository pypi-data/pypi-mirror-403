"""FastAPI application for multimedia service."""

import asyncio
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .routers import videos, thumbnails, stream, tags
from .config import settings
from .database import init_database
from .scanner import scan_directory
from .video_processor import check_dependencies


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to check Bearer token authentication for API routes."""

    async def dispatch(self, request: Request, call_next):
        # Skip auth check if no passphrase is configured
        if not settings.passphrase:
            return await call_next(request)

        # Skip auth for the auth check endpoint and static files
        path = request.url.path
        if path == "/api/auth/check" or not path.startswith("/api/"):
            return await call_next(request)

        # Check Bearer token from header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if secrets.compare_digest(token, settings.passphrase):
                return await call_next(request)

        # For stream/thumbnail endpoints, also check query param (browser video player can't set headers)
        if path.startswith("/api/stream/") or path.startswith("/api/thumbnails/"):
            token = request.query_params.get("token", "")
            if token and secrets.compare_digest(token, settings.passphrase):
                return await call_next(request)

        raise HTTPException(status_code=401, detail="Unauthorized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Check for required dependencies
    deps_ok, deps_msg = check_dependencies()
    if not deps_ok:
        print(f"\nWARNING: {deps_msg}\n")
        print("Video indexing will be skipped until dependencies are installed.\n")

    await init_database()

    # Only scan if dependencies are available
    if deps_ok:
        asyncio.create_task(scan_directory())

    yield


app = FastAPI(
    title="Multimedia",
    description="Video indexing and playback web service",
    version="0.1.0",
    lifespan=lifespan,
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

app.include_router(videos.router)
app.include_router(thumbnails.router)
app.include_router(stream.router)
app.include_router(tags.router)


@app.get("/api/auth/check")
async def check_auth(request: Request):
    """Check if authentication is required and validate token if provided."""
    requires_auth = bool(settings.passphrase)

    if not requires_auth:
        return {"requires_auth": False, "authenticated": True}

    # Check if valid token is provided
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if secrets.compare_digest(token, settings.passphrase):
            return {"requires_auth": True, "authenticated": True}

    return {"requires_auth": True, "authenticated": False}


def get_static_dir() -> Path:
    """Get the path to bundled static files."""
    try:
        import importlib.resources
        with importlib.resources.files("multimedia") as pkg_path:
            static_path = pkg_path / "static"
            if static_path.exists() and (static_path / "index.html").exists():
                return static_path
    except Exception:
        pass

    local_static = Path(__file__).parent / "static"
    if local_static.exists() and (local_static / "index.html").exists():
        return local_static

    return None


static_dir = get_static_dir()

if static_dir:
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = static_dir / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(str(favicon_path))
        return FileResponse(str(static_dir / "index.html"))

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """Serve React SPA, falling back to index.html for client-side routing."""
        if path.startswith("api/"):
            return None

        file_path = static_dir / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))

        return FileResponse(str(static_dir / "index.html"))
