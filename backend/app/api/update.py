"""In-app update endpoints: version info, check for updates, apply update.

Security: The /apply endpoint only works when running as a desktop app
(localhost). It is restricted to requests from 127.0.0.1 / ::1.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

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


def _is_localhost(request: Request) -> bool:
    """Check if the request originates from localhost."""
    client = request.client
    if not client:
        return False
    return client.host in ("127.0.0.1", "::1", "localhost")


@router.post("/apply")
async def apply_update(request: Request):
    if not _is_localhost(request):
        raise HTTPException(403, "Update can only be triggered from localhost")

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
                    _relaunch_after_exit_macos(app_path)
                    time.sleep(0.3)
                    os._exit(0)
        except Exception:
            pass

    threading.Thread(target=run_update, daemon=True).start()

    return {"success": True, "message": "Updating... the app will restart shortly."}


def _relaunch_after_exit_macos(app_path: str) -> None:
    """Spawn a detached helper that waits for this process to exit, then
    launches a fresh instance of the app.

    The helper:
      - Survives the current process exiting (start_new_session=True).
      - Polls until the parent PID is gone, so launchd no longer sees the
        bundle as running.
      - Uses `open -n` to force a new instance even if launchd briefly
        thinks the app is still running.
    """
    parent_pid = os.getpid()
    quoted_app = shlex.quote(app_path)
    helper_script = (
        f"for _ in $(seq 1 100); do "
        f"  kill -0 {parent_pid} 2>/dev/null || break; "
        f"  sleep 0.1; "
        f"done; "
        f"sleep 0.5; "
        f"open -n {quoted_app}"
    )
    subprocess.Popen(
        ["/bin/sh", "-c", helper_script],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
