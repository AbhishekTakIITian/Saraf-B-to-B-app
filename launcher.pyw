import os
import sys
import shutil
import threading
import time
import tempfile
import subprocess
import urllib.request

# Resolve resource paths for PyInstaller (sys._MEIPASS) and source runs
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

# Ensure backend directory is in Python path before importing backend modules
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import uvicorn

PORT = 8000
APP_URL = f"http://127.0.0.1:{PORT}"

def wait_for_server(url, timeout=15):
    """Wait until FastAPI is ready before opening Edge."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(f"{url}/health") as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False

def find_browser():
    """Find Microsoft Edge or Google Chrome executable to run in app mode."""
    for name in ("msedge", "msedge.exe", "chrome", "chrome.exe"):
        found = shutil.which(name)
        if found:
            return found

    candidates = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None

def start_backend():
    # Import inside thread so PostgreSQL has already been started by main()
    from api import app
    # Run uvicorn in-process (log_level="warning" prevents console spam)
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")

def main():
    # 1. Start PostgreSQL service if not already running (optional)
    subprocess.run(
        ["net", "start", "postgresql-x64-16"],
        creationflags=subprocess.CREATE_NO_WINDOW,
        capture_output=True
    )

    # 2. Start Uvicorn in a daemon thread (exits when the process exits)
    server_thread = threading.Thread(target=start_backend, daemon=True)
    server_thread.start()

    # 3. Wait for FastAPI to be responsive
    if wait_for_server(APP_URL):
        browser_exe = find_browser()
        if browser_exe:
            temp_profile = os.path.join(tempfile.gettempdir(), "DukanAppBrowserProfile")
            browser_cmd = [
                browser_exe,
                f"--app={APP_URL}",
                f"--user-data-dir={temp_profile}",
                "--no-first-run"
            ]
            # Blocks until user closes the app window
            subprocess.run(browser_cmd)
        else:
            import webbrowser
            webbrowser.open(APP_URL)
            while True:
                time.sleep(1)

if __name__ == "__main__":
    main()
