"""
api.py — FastAPI application entry point for Dukan App B-To-B.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import clients, login

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Dukan App B-To-B API")

# ── CORS ────────────────────────────────────────────────────────────────────
# Allow the Angular dev server (port 4200) to call the API.
# Restrict origins to specific domains in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
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
