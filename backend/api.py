import logging
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from routers import login, clients

logging.basicConfig(level=logging.INFO)

app = fastapi.FastAPI(title="Dukan App B-To-B API")

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
    return {"status": "healthy"}
