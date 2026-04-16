import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.api import rest, websocket, update
from backend.app.game_manager import GameManager

app = FastAPI(title="Judgement Card Game", version="0.1.0")

# CORS: only needed in dev (production serves frontend from same origin)
cors_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Shared game manager instance
game_manager = GameManager()
rest.set_manager(game_manager)
websocket.set_manager(game_manager)

app.include_router(rest.router)
app.include_router(rest.lobby_router)
app.include_router(websocket.router)
app.include_router(update.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# --- Serve frontend static files (production) ---

def _resolve_dist_dir() -> Path:
    """Find frontend/dist whether running normally or from PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "frontend" / "dist"
    return Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


DIST_DIR = _resolve_dist_dir()

if DIST_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Catch-all: serve a real file from frontend/dist if one exists at
        that path (e.g. /rangoli.svg, /favicon.png), otherwise fall back to
        index.html for SPA client-side routing.

        Without the file check, requests like /rangoli.svg returned the SPA
        HTML, the browser silently failed to render it as an image, and the
        page looked broken (no favicon, no rangoli table motif).
        """
        candidate = (DIST_DIR / full_path).resolve()
        # Guard against path traversal: candidate must stay inside DIST_DIR
        try:
            candidate.relative_to(DIST_DIR.resolve())
        except ValueError:
            return FileResponse(DIST_DIR / "index.html")
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")
