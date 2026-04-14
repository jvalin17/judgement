"""Judgement — Desktop launcher.

Starts the backend server in a background thread and opens a native
window using pywebview. Install: pip install pywebview
"""

import os
import sys
import threading
import time

import uvicorn
import webview


DEFAULT_PORT = 8000


def start_server(port: int) -> None:
    """Run uvicorn in the current thread (called as daemon)."""
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=port,
        ws="websockets",
        log_level="warning",
    )


def wait_for_server(port: int, timeout: float = 10.0) -> bool:
    """Block until the server responds or timeout."""
    import urllib.request
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.1)
    return False


def main() -> None:
    port = int(os.environ.get("JUDGEMENT_PORT", DEFAULT_PORT))
    server_url = os.environ.get("JUDGEMENT_SERVER", "")

    if not server_url:
        # Start embedded server
        server_thread = threading.Thread(
            target=start_server, args=(port,), daemon=True
        )
        server_thread.start()

        if not wait_for_server(port):
            print("Server failed to start", file=sys.stderr)
            sys.exit(1)

        server_url = f"http://127.0.0.1:{port}"

    webview.create_window(
        "Judgement",
        server_url,
        width=1024,
        height=768,
        min_size=(375, 667),
    )
    webview.start()


if __name__ == "__main__":
    main()
