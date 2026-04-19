"""In-app update endpoints: version info, check for updates, apply update.

Security: The /apply endpoint only works when running as a desktop app
(localhost). It is restricted to requests from 127.0.0.1 / ::1.

Update lifecycle (state machine, exposed via GET /api/update/status):

    idle  ──apply──>  running  ──exit 0, sha bumped──>  success  ──relaunch──> [process dies]
                          │   ──exit 0, sha unchanged─>  up_to_date
                          └── ──exit != 0 / exception─>  error

The frontend polls /status while updating so it can show before -> after
SHA on success, or the tail of the log on error. We only relaunch the
app when the SHA actually moved, so a failed git pull or build never
results in a silent "phantom" restart.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/update", tags=["update"])

GITHUB_REPO = "jvalin17/judgement"


# ---------------------------------------------------------------------------
# Update progress state (in-process, lives until os._exit on relaunch).
# ---------------------------------------------------------------------------
_state_lock = threading.Lock()
_update_state: Dict[str, Any] = {
    "state": "idle",          # idle | running | success | up_to_date | error
    "message": "",
    "before_sha": None,
    "after_sha": None,
    "log_path": None,
}


def _set_state(**kwargs: Any) -> None:
    with _state_lock:
        _update_state.update(kwargs)


def _read_state() -> Dict[str, Any]:
    with _state_lock:
        return dict(_update_state)


# ---------------------------------------------------------------------------
# Version info helpers.
# ---------------------------------------------------------------------------
def _load_version_info() -> dict:
    """Load version_info.json from bundled app or source tree."""
    if getattr(sys, "frozen", False):
        path = Path(sys._MEIPASS) / "backend" / "app" / "version_info.json"
    else:
        path = Path(__file__).resolve().parent.parent / "version_info.json"

    if path.exists():
        return json.loads(path.read_text())
    return {"git_sha": "dev", "build_date": None, "source_dir": None}


def _read_source_sha(source_dir: str) -> Optional[str]:
    """Read git_sha from the source tree's version_info.json.

    package.sh rewrites this file on every successful build, so after
    update.sh finishes we can read it to learn what SHA the *new* bundle
    was built from.
    """
    candidate = Path(source_dir) / "backend" / "app" / "version_info.json"
    if not candidate.exists():
        return None
    try:
        return json.loads(candidate.read_text()).get("git_sha")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Logging helpers.
# ---------------------------------------------------------------------------
def _build_subprocess_env() -> Dict[str, str]:
    """Build an environment for the update subprocess with a sane PATH.

    macOS launches .app bundles via launchd, which inherits a stripped
    PATH (typically `/usr/bin:/bin:/usr/sbin:/sbin`). That excludes the
    Homebrew and user-bin directories where `npm`, `node`, and many
    other build tools actually live, so `update.sh` would fail at the
    `npm run build` step with "command not found" and we'd silently
    relaunch the unchanged app. We extend the PATH to find these tools.

    Ordering matters: `/usr/bin` MUST come before `/opt/homebrew/bin`.
    The user's package.sh runs `arch -arm64 python3`, which resolves
    `python3` via PATH. The Xcode CLT Python at `/usr/bin/python3`
    (delegated to /Library/Developer/CommandLineTools/...) ships pydantic
    and is not PEP 668-locked. Homebrew's Python at /opt/homebrew/bin/
    refuses `pip install` with "externally-managed-environment", which
    breaks the rebuild. This ordering matches the user's interactive
    shell PATH where `python3` -> /usr/bin/python3 works.
    """
    env = os.environ.copy()
    extra_paths = [
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
        "/usr/local/bin",      # Intel Homebrew + many user installs
        "/usr/local/sbin",
        "/opt/homebrew/bin",   # Apple Silicon Homebrew (npm/node live here)
        "/opt/homebrew/sbin",
    ]
    existing = env.get("PATH", "").split(":")
    merged = []
    seen = set()
    for entry in extra_paths + existing:
        if entry and entry not in seen:
            merged.append(entry)
            seen.add(entry)
    env["PATH"] = ":".join(merged)
    return env


def _open_log_file() -> Path:
    """Create a timestamped log file under the platform's logs directory."""
    if sys.platform == "darwin":
        log_dir = Path.home() / "Library" / "Logs" / "Judgement"
    else:
        log_dir = Path.home() / ".judgement" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return log_dir / f"update-{timestamp}.log"


def _tail(path: Path, lines: int = 20) -> str:
    """Return the last N lines of a file, or empty string on any failure."""
    try:
        with path.open() as fh:
            return "".join(fh.readlines()[-lines:])
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Endpoints.
# ---------------------------------------------------------------------------
@router.get("/version")
async def get_version():
    info = _load_version_info()
    return {
        "git_sha": info.get("git_sha", "dev"),
        "build_date": info.get("build_date"),
    }


@router.get("/status")
async def get_update_status():
    """Return the current update progress (polled by the UI while updating)."""
    return _read_state()


def _ci_passing_for_sha(sha: str) -> bool:
    """Check if CI tests are passing for the given commit SHA.

    Returns True if the combined status is 'success', False otherwise.
    If the API call fails or there are no statuses, returns True to
    avoid blocking updates due to network issues.
    """
    import urllib.request
    import urllib.error
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{sha}/check-runs"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Judgement-App",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        check_runs = data.get("check_runs", [])
        if not check_runs:
            return True  # no CI configured, don't block

        for run in check_runs:
            if run.get("status") != "completed":
                return False  # still running, don't offer yet
            if run.get("conclusion") not in ("success", "skipped"):
                return False  # at least one check failed
        return True
    except Exception:
        return True  # network error — don't block updates


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
        full_sha = data["sha"]
        latest_message = data["commit"]["message"].split("\n")[0]

        has_new_commit = current_sha != latest_sha and current_sha != "dev"
        ci_ok = _ci_passing_for_sha(full_sha) if has_new_commit else True

        return {
            "update_available": has_new_commit and ci_ok,
            "current_sha": current_sha,
            "latest_sha": latest_sha,
            "latest_message": latest_message,
            "ci_status": "passing" if ci_ok else "failing",
            "error": None,
        }
    except Exception as exc:
        return {
            "update_available": False,
            "current_sha": current_sha,
            "latest_sha": None,
            "latest_message": None,
            "ci_status": None,
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

    if _read_state()["state"] == "running":
        return {"success": False, "message": "An update is already in progress."}

    info = _load_version_info()
    source_dir = info.get("source_dir")

    if not source_dir or not Path(source_dir).is_dir():
        return {"success": False, "message": "Source directory not found. Run update from terminal: ./scripts/update.sh"}

    update_script = Path(source_dir) / "scripts" / "update.sh"
    if not update_script.exists():
        return {"success": False, "message": "Update script not found."}

    before_sha = info.get("git_sha", "dev")
    log_path = _open_log_file()
    _set_state(
        state="running",
        message="Pulling latest changes and rebuilding...",
        before_sha=before_sha,
        after_sha=None,
        log_path=str(log_path),
    )

    threading.Thread(
        target=_run_update,
        args=(str(update_script), source_dir, before_sha, log_path),
        daemon=True,
    ).start()

    return {"success": True, "message": "Updating... watch the Updates section for progress."}


def _run_update(
    update_script: str,
    source_dir: str,
    before_sha: str,
    log_path: Path,
) -> None:
    """Background worker: run update.sh, verify the SHA bumped, then relaunch.

    Critical correctness point: we ONLY relaunch when (a) the script exited
    cleanly AND (b) source_dir/backend/app/version_info.json now contains a
    different SHA. If either check fails we leave the old app running and
    surface the failure via /api/update/status, so the user is never told
    "updated!" without something actually changing.
    """
    try:
        env = _build_subprocess_env()
        with log_path.open("w") as log_file:
            log_file.write(f"=== Update started at {datetime.now().isoformat()} ===\n")
            log_file.write(f"Before SHA: {before_sha}\n")
            log_file.write(f"Source dir: {source_dir}\n")
            log_file.write(f"PATH: {env['PATH']}\n\n")
            log_file.flush()

            result = subprocess.run(
                ["bash", update_script],
                cwd=source_dir,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                timeout=600,
                env=env,
            )

        if result.returncode != 0:
            _set_state(
                state="error",
                message=(
                    f"Update script failed (exit {result.returncode}). "
                    f"Last lines of {log_path.name}:\n{_tail(log_path, 15)}"
                ),
            )
            return

        after_sha = _read_source_sha(source_dir) or "unknown"
        _set_state(after_sha=after_sha)

        if after_sha == before_sha:
            _set_state(
                state="up_to_date",
                message=(
                    f"Already on the latest version ({before_sha}). "
                    "No restart needed."
                ),
            )
            return

        _set_state(
            state="success",
            message=f"Updated {before_sha} → {after_sha}. Restarting...",
        )

        # Give the UI ~2.5s to poll /status and render the success state
        # before we kill this process.
        if sys.platform == "darwin":
            app_path = "/Applications/Judgement.app"
            if Path(app_path).exists():
                time.sleep(2.5)
                _relaunch_after_exit_macos(app_path)
                time.sleep(0.3)
                os._exit(0)
    except subprocess.TimeoutExpired:
        _set_state(
            state="error",
            message=f"Update timed out after 10 minutes. See {log_path}.",
        )
    except Exception as exc:
        _set_state(
            state="error",
            message=f"Update failed: {exc}. See {log_path}.",
        )


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
