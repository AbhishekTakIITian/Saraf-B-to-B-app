"""
api.py — FastAPI application entry point for Dukan App B-To-B.
"""

import logging
import mimetypes
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from routers import clients, login
from utils.db_utils import cleanup_completed_data_entries_after_3_days

# Ensure Windows registry doesn't cause .js files to be served as text/plain
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/x-icon", ".ico")


def _runtime_log_dir() -> Path:
    """Return the directory where runtime log files should be written."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # backend/api.py -> project root
    return Path(__file__).resolve().parent.parent


def _configure_backend_logging() -> None:
    """Configure backend logging to write all backend logs to logger.txt."""
    log_path = _runtime_log_dir() / "logger.txt"
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not any(
        isinstance(handler, logging.FileHandler)
        and Path(getattr(handler, "baseFilename", "")) == log_path
        for handler in root_logger.handlers
    ):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        root_logger.addHandler(file_handler)


_configure_backend_logging()


@asynccontextmanager
async def lifespan(app: FastAPI): #pylint: disable=unused-argument redefined-outer-name
    """Lifespan context manager for FastAPI app."""
    # Startup tasks
    try:
        await cleanup_completed_data_entries_after_3_days()
    except Exception: #pylint: disable=broad-except
        logging.exception(
            "[Startup] Completed data entry cleanup failed; continuing app startup."
        )
    yield
    # Shutdown tasks (if any) can be added here

app = FastAPI(title="Dukan App B-To-B API", lifespan=lifespan)
# ── CORS ────────────────────────────────────────────────────────────────────
# Allow Angular dev server (port 4200) as well as the local backend origin (port 8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(login.router)
app.include_router(clients.router)


@app.get("/health")
async def health_check():
    """Health check endpoint returning service status."""
    return {"status": "healthy"}


# ── SPA Frontend Serving ────────────────────────────────────────────────────
# Supports running from source and bundled executable (PyInstaller)
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FRONTEND_CANDIDATES = [
    # 1. Bundled via PyInstaller (--add-data "...;dist")
    os.path.join(BASE_DIR, "dist"),
    # 2. Local dev build in repo
    os.path.join(BASE_DIR, "frontend", "dukan-app-saraf", "dist", "dukan-app-saraf", "browser"),
]

FRONTEND_DIR = None
for candidate in FRONTEND_CANDIDATES:
    if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, "index.html")):
        FRONTEND_DIR = candidate
        break

if FRONTEND_DIR:
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve static files or fallback to index.html for Angular SPA routing."""
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            media_type, _ = mimetypes.guess_type(file_path)
            if file_path.endswith(".js"):
                media_type = "application/javascript"
            elif file_path.endswith(".css"):
                media_type = "text/css"
            return FileResponse(file_path, media_type=media_type)

        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file, media_type="text/html")

        return {"detail": "Frontend index.html not found"}
