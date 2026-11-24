import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

# Resolve resource paths for PyInstaller (sys._MEIPASS) and source runs
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

_BACKEND_CANDIDATES = [
    os.path.join(BASE_DIR, "backend"),
    os.path.join(BASE_DIR, "system"),
]
BACKEND_DIR = None
for _candidate in _BACKEND_CANDIDATES:
    if os.path.isfile(os.path.join(_candidate, "api.py")):
        BACKEND_DIR = _candidate
        break
if BACKEND_DIR is None:
    BACKEND_DIR = os.path.join(BASE_DIR, "backend")

# Ensure backend directory is in Python path before importing backend modules
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import uvicorn

PORT = 8000
APP_URL = f"http://127.0.0.1:{PORT}"


def _runtime_dir() -> Path:
    """Return the directory where runtime logs should be written."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _configure_launcher_logger() -> logging.Logger:
    """Configure a separate logger for the launcher process."""
    logger = logging.getLogger("launcher")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_path = _runtime_dir() / "launcher.log"
    if not any(
        isinstance(handler, logging.FileHandler)
        and Path(getattr(handler, "baseFilename", "")) == log_path
        for handler in logger.handlers
    ):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        logger.addHandler(file_handler)

    return logger


launcher_logger = _configure_launcher_logger()


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
    """Start the backend server in-process and capture failures in launcher logs."""
    try:
        launcher_logger.info("Resolved backend directory: %s", BACKEND_DIR)
        # Import inside thread so PostgreSQL has already been started by main()
        from api import app

        launcher_logger.info("Starting backend server on %s", APP_URL)
        for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            logging.getLogger(logger_name).setLevel(logging.INFO)

        uvicorn.run(
            app,
            host="127.0.0.1",
            port=PORT,
            log_level="info",
            log_config=None,
            access_log=True,
        )
    except Exception:
        launcher_logger.exception(
            "Backend failed to start (BACKEND_DIR=%s, exists=%s)",
            BACKEND_DIR,
            os.path.isdir(BACKEND_DIR),
        )

def main():
    try:
        launcher_logger.info("Launcher starting (BASE_DIR=%s, BACKEND_DIR=%s)", BASE_DIR, BACKEND_DIR)

        # 1. Start PostgreSQL service if not already running (optional)
        result = subprocess.run(
            ["net", "start", "postgresql-x64-16"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            launcher_logger.info("PostgreSQL service start command completed successfully")
        else:
            launcher_logger.warning(
                "PostgreSQL service start command returned %s. stdout=%s stderr=%s",
                result.returncode,
                (result.stdout or "").strip(),
                (result.stderr or "").strip(),
            )

        # 2. Start Uvicorn in a daemon thread (exits when the process exits)
        server_thread = threading.Thread(target=start_backend, daemon=True)
        server_thread.start()
        launcher_logger.info("Backend thread started; waiting for %s", APP_URL)

        # 3. Wait for FastAPI to be responsive
        if wait_for_server(APP_URL):
            launcher_logger.info("Backend is ready at %s", APP_URL)
            browser_exe = find_browser()
            if browser_exe:
                temp_profile = os.path.join(tempfile.gettempdir(), "DukanAppBrowserProfile")
                browser_cmd = [
                    browser_exe,
                    f"--app={APP_URL}",
                    f"--user-data-dir={temp_profile}",
                    "--no-first-run"
                ]
                launcher_logger.info("Launching browser: %s", browser_exe)
                # Blocks until user closes the app window
                subprocess.run(browser_cmd)
                launcher_logger.info("Browser process exited; launcher shutting down")
            else:
                launcher_logger.warning(
                    "No supported browser executable found; opening default browser"
                )
                import webbrowser

                webbrowser.open(APP_URL)
                while True:
                    time.sleep(1)
        else:
            launcher_logger.error(
                "Backend did not become ready within timeout at %s", APP_URL
            )
    except Exception:
        launcher_logger.exception("Launcher encountered an unrecoverable error")


if __name__ == "__main__":
    main()
