import os
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.api import rest, websocket, update, data_sharing
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
app.include_router(data_sharing.router)


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

_INDEX_HEADERS = {"Cache-Control": "no-cache, must-revalidate"}
_ASSET_HEADERS = {"Cache-Control": "public, max-age=31536000, immutable"}


if DIST_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="static")

    # Vite emits content-hashed filenames under /assets, so the StaticFiles mount
    # above is safe to cache aggressively. Everything else (index.html, /favicon,
    # SPA fallbacks) MUST revalidate or iOS Safari will pin a stale bundle and
    # users will run pre-fix code for days. (We hit this in the iPhone 17
    # diagnosis on 2026-04-30.)
    @app.middleware("http")
    async def _set_static_cache_headers(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/assets/"):
            response.headers.setdefault("Cache-Control", _ASSET_HEADERS["Cache-Control"])
        return response

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
        try:
            candidate.relative_to(DIST_DIR.resolve())
        except ValueError:
            return FileResponse(DIST_DIR / "index.html", headers=_INDEX_HEADERS)
        if full_path and candidate.is_file():
            return FileResponse(candidate, headers=_INDEX_HEADERS)
        return FileResponse(DIST_DIR / "index.html", headers=_INDEX_HEADERS)
