"""
api.py — FastAPI application entry point for Dukan App B-To-B.
"""

import logging
import mimetypes
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from routers import clients, login

# Ensure Windows registry doesn't cause .js files to be served as text/plain
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/x-icon", ".ico")

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Dukan App B-To-B API")

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
