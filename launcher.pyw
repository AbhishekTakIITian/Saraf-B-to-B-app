import subprocess
import time
import urllib.request
import os
import tempfile

PORT = 8000
APP_URL = f"http://127.0.0.1:{PORT}"
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")

def wait_for_server(url, timeout=15):
    """Wait until FastAPI is ready before opening the window."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(f"{url}/api/health")
            return True
        except Exception:
            time.sleep(0.3)
    return False

def main():
    # 1. Start PostgreSQL service if it isn't already running (optional)
    # Replace 'postgresql-x64-16' with your actual Windows service name
    subprocess.run(
        ["net", "start", "postgresql-x64-16"],
        creationflags=subprocess.CREATE_NO_WINDOW,
        capture_output=True
    )

    # 2. Start the FastAPI backend silently
    backend_process = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=BACKEND_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    try:
        # 3. Wait for backend to boot, then open Microsoft Edge in App Mode
        if wait_for_server(APP_URL):
            temp_profile = os.path.join(tempfile.gettempdir(), "MyWindowsAppEdgeProfile")
            edge_cmd = [
                "msedge.exe",
                f"--app={APP_URL}",
                f"--user-data-dir={temp_profile}",
                "--no-first-run"
            ]
            # subprocess.run blocks here until you close the app window!
            subprocess.run(edge_cmd)
    finally:
        # 4. Clean up: Kill the Python backend when the window closes
        backend_process.terminate()
        backend_process.wait()

if __name__ == "__main__":
    main()
