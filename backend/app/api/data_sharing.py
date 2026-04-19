"""Community data sharing endpoints.

Allows players to share anonymized ML training data (winner decisions)
with the community via GitHub Releases, and download community data
to improve their local AI.

Data shared: numeric feature vectors + labels only. No player IDs,
names, or identifiable information.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter

from backend.app.ml.data_store import get_default_store
from backend.app.ml.learning.decision_collector import get_bid_data_file, get_play_data_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["data-sharing"])

GITHUB_REPO = "jvalin17/judgement"
RELEASE_TAG = "community-data"

# Track upload state
_state_lock = threading.Lock()
_share_state: Dict[str, Any] = {"state": "idle", "message": ""}


def _set_state(**kwargs: Any) -> None:
    with _state_lock:
        _share_state.update(kwargs)


def _read_state() -> Dict[str, Any]:
    with _state_lock:
        return dict(_share_state)


def _get_github_token() -> Optional[str]:
    """Get GitHub PAT from environment. Returns None if not configured."""
    return os.environ.get("JUDGEMENT_GITHUB_TOKEN")


def _get_community_data_dir() -> Path:
    """Directory for community-downloaded data, separate from local data."""
    data_dir = Path(get_bid_data_file()).parent / "community"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/share/preview")
async def share_preview():
    """Return summary of what would be shared — counts only, no raw data."""
    store = get_default_store()
    bid_count = store.example_count(get_bid_data_file())
    play_count = store.example_count(get_play_data_file())

    # Count how many are human-origin (if metadata includes strategy_type)
    bid_examples = store.load_examples(get_bid_data_file())
    play_examples = store.load_examples(get_play_data_file())
    human_bids = sum(1 for ex in bid_examples if ex.get("strategy_type") == "human")
    human_plays = sum(1 for ex in play_examples if ex.get("strategy_type") == "human")

    return {
        "bid_decisions": bid_count,
        "play_decisions": play_count,
        "human_bid_decisions": human_bids,
        "human_play_decisions": human_plays,
        "total": bid_count + play_count,
        "description": "Numeric feature vectors and labels only. No player names or identifiable data.",
    }


@router.post("/share")
async def share_data():
    """Upload local winner decisions to GitHub release as community data."""
    token = _get_github_token()
    if not token:
        return {
            "success": False,
            "message": "Data sharing is not configured. Set JUDGEMENT_GITHUB_TOKEN environment variable.",
        }

    if _read_state()["state"] == "uploading":
        return {"success": False, "message": "Upload already in progress."}

    _set_state(state="uploading", message="Preparing data...")

    threading.Thread(target=_upload_data, args=(token,), daemon=True).start()

    return {"success": True, "message": "Uploading..."}


@router.get("/share/status")
async def share_status():
    """Poll upload progress."""
    return _read_state()


@router.get("/community/check")
async def check_community_data():
    """Check if community data is available on GitHub."""
    try:
        import urllib.request

        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{RELEASE_TAG}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Judgement-App",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        assets = data.get("assets", [])
        bid_asset = next((a for a in assets if a["name"] == "bid_decisions.jsonl"), None)
        play_asset = next((a for a in assets if a["name"] == "play_decisions.jsonl"), None)

        return {
            "available": bool(bid_asset or play_asset),
            "bid_size": bid_asset["size"] if bid_asset else 0,
            "play_size": play_asset["size"] if play_asset else 0,
            "updated_at": data.get("published_at"),
            "error": None,
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}


@router.post("/community/download")
async def download_community_data():
    """Download community data from GitHub release and merge with local data."""
    try:
        import urllib.request

        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{RELEASE_TAG}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Judgement-App",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        assets = data.get("assets", [])
        downloaded = 0

        for asset in assets:
            if asset["name"] not in ("bid_decisions.jsonl", "play_decisions.jsonl"):
                continue

            download_url = asset["browser_download_url"]
            dl_req = urllib.request.Request(download_url, headers={
                "User-Agent": "Judgement-App",
            })
            with urllib.request.urlopen(dl_req, timeout=30) as dl_resp:
                content = dl_resp.read().decode("utf-8")

            # Merge: append community examples to local data files
            if asset["name"] == "bid_decisions.jsonl":
                target = get_bid_data_file()
            else:
                target = get_play_data_file()

            # Parse and deduplicate by checking existing features+labels
            existing = get_default_store().load_examples(target)
            existing_keys = {
                (tuple(ex["features"]), ex["label"])
                for ex in existing
            }

            new_count = 0
            with open(target, "a") as fh:
                for line in content.strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        key = (tuple(entry["features"]), entry["label"])
                        if key not in existing_keys:
                            fh.write(json.dumps(entry) + "\n")
                            existing_keys.add(key)
                            new_count += 1
                    except (json.JSONDecodeError, KeyError):
                        continue

            downloaded += new_count
            logger.info("Merged %d new examples from community %s", new_count, asset["name"])

        return {
            "success": True,
            "message": f"Downloaded {downloaded} new examples from community data.",
            "examples_added": downloaded,
        }
    except Exception as exc:
        logger.error("Community data download failed: %s", exc)
        return {"success": False, "message": str(exc), "examples_added": 0}


# ---------------------------------------------------------------------------
# Background upload worker
# ---------------------------------------------------------------------------

def _upload_data(token: str) -> None:
    """Background worker: upload local JSONL data to GitHub release."""
    try:
        import urllib.request

        store = get_default_store()
        bid_examples = store.load_examples(get_bid_data_file())
        play_examples = store.load_examples(get_play_data_file())

        if not bid_examples and not play_examples:
            _set_state(state="idle", message="No data to share.")
            return

        # Ensure release exists
        release_id = _ensure_release(token)
        if not release_id:
            _set_state(state="error", message="Could not create GitHub release for community data.")
            return

        # Upload each file
        for filename, examples in [("bid_decisions.jsonl", bid_examples), ("play_decisions.jsonl", play_examples)]:
            if not examples:
                continue
            content = "\n".join(json.dumps(ex) for ex in examples) + "\n"
            _upload_asset(token, release_id, filename, content.encode("utf-8"))

        total = len(bid_examples) + len(play_examples)
        _set_state(state="success", message=f"Shared {total} examples with the community.")
        logger.info("Uploaded %d examples to GitHub release", total)

    except Exception as exc:
        logger.error("Data upload failed: %s", exc)
        _set_state(state="error", message=f"Upload failed: {exc}")


def _ensure_release(token: str) -> Optional[int]:
    """Get or create the community-data release. Returns release ID."""
    import urllib.request
    import urllib.error

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
        "User-Agent": "Judgement-App",
    }

    # Check if release exists
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{RELEASE_TAG}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data["id"]
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise

    # Create release
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    body = json.dumps({
        "tag_name": RELEASE_TAG,
        "name": "Community Training Data",
        "body": "Anonymized game decision data shared by players to improve AI.",
        "draft": False,
        "prerelease": False,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        **headers,
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        return data["id"]


def _upload_asset(token: str, release_id: int, filename: str, content: bytes) -> None:
    """Upload or replace a release asset."""
    import urllib.request
    import urllib.error

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
        "User-Agent": "Judgement-App",
    }

    # Delete existing asset with same name (if any)
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/{release_id}/assets"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        assets = json.loads(resp.read())

    for asset in assets:
        if asset["name"] == filename:
            del_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/assets/{asset['id']}"
            del_req = urllib.request.Request(del_url, method="DELETE", headers=headers)
            urllib.request.urlopen(del_req, timeout=10)
            break

    # Upload new asset
    upload_url = f"https://uploads.github.com/repos/{GITHUB_REPO}/releases/{release_id}/assets?name={filename}"
    req = urllib.request.Request(upload_url, data=content, headers={
        **headers,
        "Content-Type": "application/octet-stream",
    })
    urllib.request.urlopen(req, timeout=30)
