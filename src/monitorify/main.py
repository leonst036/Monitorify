import subprocess
import sys
import os
from monitorify import config
from monitorify.ui.tui.tui import MonitorifyApp


def daemon_already_running() -> bool:
    """Check if a daemon process from a previous run is still alive."""
    if not config.DAEMON_PIDFILE.exists():
        return False
    try:
        pid = int(config.DAEMON_PIDFILE.read_text().strip())
        # Signal 0 checks if the process exists without killing it
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        config.DAEMON_PIDFILE.unlink(missing_ok=True)
        return False


def start_daemon() -> subprocess.Popen | None:
    """Start the daemon as a background subprocess if not already running."""
    if daemon_already_running():
        return None

    proc = subprocess.Popen(
        [sys.executable, "-m", "monitorify.daemon"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    config.DAEMON_PIDFILE.write_text(str(proc.pid))
    return proc


def cli():
    """Main CLI entrypoint for Monitorify."""
    daemon = start_daemon()
    try:
        app = MonitorifyApp()
        app.run()
    finally:
        if daemon is not None:
            daemon.terminate()
            try:
                daemon.wait(timeout=2)
            except subprocess.TimeoutExpired:
                daemon.kill()
            config.DAEMON_PIDFILE.unlink(missing_ok=True)


if __name__ == "__main__":
    cli()
