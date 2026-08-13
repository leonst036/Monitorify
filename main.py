import subprocess
import sys
import os
from pathlib import Path
from ui.tui.tui import MonitorifyApp

DAEMON_PIDFILE = Path(__file__).parent / ".daemon.pid"


def daemon_already_running() -> bool:
    """Check if a daemon process from a previous run is still alive."""
    if not DAEMON_PIDFILE.exists():
        return False
    try:
        pid = int(DAEMON_PIDFILE.read_text().strip())
        # Signal 0 checks if the process exists without killing it
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        DAEMON_PIDFILE.unlink(missing_ok=True)
        return False


def start_daemon() -> subprocess.Popen | None:
    """Start the daemon as a background subprocess if not already running."""
    if daemon_already_running():
        return None

    daemon_script = Path(__file__).parent / "daemon.py"
    proc = subprocess.Popen(
        [sys.executable, str(daemon_script)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    DAEMON_PIDFILE.write_text(str(proc.pid))
    return proc


if __name__ == "__main__":
    daemon = start_daemon()
    try:
        app = MonitorifyApp()
        app.run()
    finally:
        if daemon is not None:
            daemon.terminate()
            daemon.wait()
            DAEMON_PIDFILE.unlink(missing_ok=True)
