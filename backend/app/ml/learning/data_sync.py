"""Server-side data synchronization with GitHub community data.

Handles:
- Downloading community data on server startup
- Periodic background sync (upload server data + download community updates)
- Consent-aware filtering for uploads

This module is used by the server (JUDGEMENT_SERVER_MODE=1) to keep SmartHardAI
data fresh. Desktop users continue using the REST endpoints in data_sharing.py.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import urllib.error
import urllib.request
from typing import Optional

from backend.app.ml.data_store import get_default_store
from backend.app.ml.learning.decision_collector import get_bid_data_file, get_play_data_file

logger = logging.getLogger(__name__)

GITHUB_REPO = "jvalin17/judgement"
RELEASE_TAG = "community-data"

# Track accumulated examples since last upload
_upload_counter_lock = threading.Lock()
_examples_since_last_upload = 0
UPLOAD_THRESHOLD = 50


def increment_upload_counter(count: int = 1) -> bool:
    """Increment the counter of new consented examples. Returns True if threshold reached."""
    global _examples_since_last_upload
    with _upload_counter_lock:
        _examples_since_last_upload += count
        return _examples_since_last_upload >= UPLOAD_THRESHOLD


def reset_upload_counter() -> None:
    global _examples_since_last_upload
    with _upload_counter_lock:
        _examples_since_last_upload = 0


def _get_github_token() -> Optional[str]:
    return os.environ.get("JUDGEMENT_GITHUB_TOKEN") or None


def _github_headers(token: Optional[str] = None) -> dict:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Judgement-App",
    }
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


# ---------------------------------------------------------------------------
# Download community data
# ---------------------------------------------------------------------------

def download_community_data() -> int:
    """Download community data from GitHub and merge into local files.

    Returns the number of new examples added.
    """
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{RELEASE_TAG}"
        req = urllib.request.Request(url, headers=_github_headers())
        with urllib.request.urlopen(req, timeout=15) as resp:
            release_data = json.loads(resp.read())

        assets = release_data.get("assets", [])
        total_new = 0

        for asset in assets:
            if asset["name"] not in ("bid_decisions.jsonl", "play_decisions.jsonl"):
                continue

            target_file = get_bid_data_file() if asset["name"] == "bid_decisions.jsonl" else get_play_data_file()
            new_count = _download_and_merge_asset(asset, target_file)
            total_new += new_count

        if total_new > 0:
            get_default_store().invalidate_cache()
            logger.info("Community sync: merged %d new examples", total_new)
        else:
            logger.info("Community sync: no new examples")

        return total_new

    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            logger.info("No community data release found on GitHub")
            return 0
        logger.error("Community data download failed: HTTP %d", exc.code)
        return 0
    except Exception as exc:
        logger.error("Community data download failed: %s", exc)
        return 0


def _download_and_merge_asset(asset: dict, target_file: str) -> int:
    """Download a single asset and merge-deduplicate into the target file."""
    download_url = asset["browser_download_url"]
    req = urllib.request.Request(download_url, headers={"User-Agent": "Judgement-App"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8")

    store = get_default_store()
    existing = store.load_examples(target_file)
    existing_keys = {(tuple(ex["features"]), ex["label"]) for ex in existing}

    new_count = 0
    directory = os.path.dirname(target_file)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(target_file, "a") as file_handle:
        for line in content.strip().split("\n"):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                key = (tuple(entry["features"]), entry["label"])
                if key not in existing_keys:
                    file_handle.write(json.dumps(entry) + "\n")
                    existing_keys.add(key)
                    new_count += 1
            except (json.JSONDecodeError, KeyError):
                continue

    return new_count


# ---------------------------------------------------------------------------
# Upload server data (consent-filtered)
# ---------------------------------------------------------------------------

def upload_server_data(consent_only: bool = True) -> bool:
    """Upload server's ML data to GitHub release.

    When consent_only=True, only uploads examples that have share_consent metadata.
    Returns True on success.
    """
    token = _get_github_token()
    if not token:
        logger.debug("No GitHub token configured, skipping upload")
        return False

    try:
        store = get_default_store()
        bid_examples = store.load_examples(get_bid_data_file())
        play_examples = store.load_examples(get_play_data_file())

        if consent_only:
            bid_examples = [ex for ex in bid_examples if ex.get("share_consent")]
            play_examples = [ex for ex in play_examples if ex.get("share_consent")]

        if not bid_examples and not play_examples:
            logger.info("No consented data to upload")
            return True

        release_id = _ensure_release(token)
        if not release_id:
            logger.error("Could not create/find GitHub release")
            return False

        for filename, examples in [("bid_decisions.jsonl", bid_examples), ("play_decisions.jsonl", play_examples)]:
            if not examples:
                continue
            content = "\n".join(json.dumps(ex) for ex in examples) + "\n"
            _upload_asset(token, release_id, filename, content.encode("utf-8"))

        total = len(bid_examples) + len(play_examples)
        logger.info("Uploaded %d consented examples to GitHub release", total)
        reset_upload_counter()
        return True

    except Exception as exc:
        logger.error("Server data upload failed: %s", exc)
        return False


def _ensure_release(token: str) -> Optional[int]:
    """Get or create the community-data release. Returns release ID."""
    headers = _github_headers(token)

    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{RELEASE_TAG}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())["id"]
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise

    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    body = json.dumps({
        "tag_name": RELEASE_TAG,
        "name": "Community Training Data",
        "body": "Anonymized game decision data shared by players to improve AI.",
        "draft": False,
        "prerelease": False,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={**headers, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())["id"]


def _upload_asset(token: str, release_id: int, filename: str, content: bytes) -> None:
    """Upload or replace a release asset."""
    headers = _github_headers(token)

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

    upload_url = f"https://uploads.github.com/repos/{GITHUB_REPO}/releases/{release_id}/assets?name={filename}"
    req = urllib.request.Request(upload_url, data=content, headers={**headers, "Content-Type": "application/octet-stream"})
    urllib.request.urlopen(req, timeout=30)


# ---------------------------------------------------------------------------
# Periodic sync (server mode only)
# ---------------------------------------------------------------------------

async def run_periodic_sync(interval_minutes: int = 60) -> None:
    """Background task: periodically download community data and upload server data."""
    while True:
        await asyncio.sleep(interval_minutes * 60)
        try:
            logger.info("Periodic sync: downloading community data")
            download_community_data()
            logger.info("Periodic sync: uploading server data")
            upload_server_data(consent_only=True)
        except Exception as exc:
            logger.error("Periodic sync failed: %s", exc)
