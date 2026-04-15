"""In-app update endpoints: version info, check for updates, apply update."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter

router = APIRouter(prefix="/api/update", tags=["update"])

GITHUB_REPO = "jvalin17/judgement"


def _load_version_info() -> dict:
    """Load version_info.json from bundled app or source tree."""
    if getattr(sys, "frozen", False):
        path = Path(sys._MEIPASS) / "backend" / "app" / "version_info.json"
    else:
        path = Path(__file__).resolve().parent.parent / "version_info.json"

    if path.exists():
        return json.loads(path.read_text())
    return {"git_sha": "dev", "build_date": None, "source_dir": None}


@router.get("/version")
async def get_version():
    info = _load_version_info()
    return {
        "git_sha": info.get("git_sha", "dev"),
        "build_date": info.get("build_date"),
    }


@router.get("/check")
async def check_for_update():
    info = _load_version_info()
    current_sha = info.get("git_sha", "dev")

    try:
        import urllib.request
        url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/main"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Judgement-App",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        latest_sha = data["sha"][:7]
        latest_message = data["commit"]["message"].split("\n")[0]

        return {
            "update_available": current_sha != latest_sha and current_sha != "dev",
            "current_sha": current_sha,
            "latest_sha": latest_sha,
            "latest_message": latest_message,
            "error": None,
        }
    except Exception as exc:
        return {
            "update_available": False,
            "current_sha": current_sha,
            "latest_sha": None,
            "latest_message": None,
            "error": str(exc),
        }


@router.post("/apply")
async def apply_update():
    info = _load_version_info()
    source_dir = info.get("source_dir")

    if not source_dir or not Path(source_dir).is_dir():
        return {"success": False, "message": "Source directory not found. Run update from terminal: ./scripts/update.sh"}

    update_script = Path(source_dir) / "scripts" / "update.sh"
    if not update_script.exists():
        return {"success": False, "message": "Update script not found."}

    def run_update():
        """Run update in background, then relaunch the app."""
        try:
            subprocess.run(
                ["bash", str(update_script)],
                cwd=source_dir,
                timeout=300,
            )
            # Relaunch the app after update
            if sys.platform == "darwin":
                app_path = "/Applications/Judgement.app"
                if Path(app_path).exists():
                    time.sleep(1)
                    subprocess.Popen(["open", app_path])
                    time.sleep(0.5)
                    import os
                    os._exit(0)
        except Exception:
            pass

    threading.Thread(target=run_update, daemon=True).start()

    return {"success": True, "message": "Updating... the app will restart shortly."}
