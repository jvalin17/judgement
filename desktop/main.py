"""Judgement — Desktop app entry point.

When frozen (PyInstaller bundle): runs server in-thread, opens native window.
When run from source: starts server as subprocess to avoid arch conflicts.

Usage:
    # From source (./play calls this with JUDGEMENT_SERVER set)
    JUDGEMENT_SERVER=http://127.0.0.1:8000 python3 desktop/main.py

    # From PyInstaller bundle (double-click Judgement.app)
    # Server runs in-thread, no external dependencies needed
"""

import os
import subprocess
import sys
import threading
import time


DEFAULT_PORT = 8000


def _is_frozen() -> bool:
    """True when running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def start_server_thread(port: int) -> threading.Thread:
    """Run uvicorn in a daemon thread (for PyInstaller bundles)."""
    import uvicorn

    def run():
        uvicorn.run(
            "backend.app.main:app",
            host="127.0.0.1",
            port=port,
            ws="websockets",
            log_level="warning",
        )

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread


def start_server_process(port: int) -> subprocess.Popen:
    """Launch uvicorn as a separate process (for dev/source mode)."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.app.main:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--ws", "websockets",
        "--log-level", "warning",
    ]

    # On macOS Apple Silicon, force matching arch for pydantic_core
    if sys.platform == "darwin":
        cmd = ["arch", "-x86_64"] + cmd

    return subprocess.Popen(cmd, cwd=project_root, stderr=subprocess.PIPE)


def wait_for_server(port: int, timeout: float = 15.0) -> bool:
    """Block until the server responds or timeout."""
    import urllib.request
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def main() -> None:
    import webview

    port = int(os.environ.get("JUDGEMENT_PORT", DEFAULT_PORT))
    server_url = os.environ.get("JUDGEMENT_SERVER", "")
    server_proc = None

    if not server_url:
        if _is_frozen():
            # PyInstaller bundle: run server in-thread (same process, same arch)
            start_server_thread(port)
        else:
            # Dev/source: run as subprocess to avoid arch conflicts
            server_proc = start_server_process(port)

        if not wait_for_server(port):
            if server_proc and server_proc.poll() is not None:
                stderr_output = server_proc.stderr.read().decode() if server_proc.stderr else ""
                print(f"Server failed to start:\n{stderr_output}", file=sys.stderr)
            else:
                if server_proc:
                    server_proc.terminate()
                print("Server failed to respond within timeout", file=sys.stderr)
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

    # Clean up server process when window closes
    if server_proc and server_proc.poll() is None:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()


if __name__ == "__main__":
    main()
