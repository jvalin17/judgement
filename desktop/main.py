"""Judgement — Desktop window launcher.

Opens a native pywebview window pointing at a running server.
The server is started separately (by ./play) to avoid architecture
conflicts between pyobjc (arm64) and pydantic_core (x86_64) on
macOS with Rosetta.

Usage:
    JUDGEMENT_SERVER=http://127.0.0.1:8000 python3 desktop/main.py
"""

import os
import subprocess
import sys
import time

import webview


DEFAULT_PORT = 8000


def start_server_process(port: int) -> subprocess.Popen:
    """Launch uvicorn as a separate process using arch -x86_64 on macOS."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.app.main:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--ws", "websockets",
        "--log-level", "warning",
    ]

    # On macOS Apple Silicon, force x86_64 to match pydantic_core wheels
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
    port = int(os.environ.get("JUDGEMENT_PORT", DEFAULT_PORT))
    server_url = os.environ.get("JUDGEMENT_SERVER", "")
    server_proc = None

    if not server_url:
        # Standalone mode: start server ourselves with arch fix
        server_proc = start_server_process(port)

        if not wait_for_server(port):
            if server_proc.poll() is not None:
                stderr_output = server_proc.stderr.read().decode() if server_proc.stderr else ""
                print(f"Server failed to start:\n{stderr_output}", file=sys.stderr)
            else:
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

    # Clean up server when window closes
    if server_proc and server_proc.poll() is None:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()


if __name__ == "__main__":
    main()
