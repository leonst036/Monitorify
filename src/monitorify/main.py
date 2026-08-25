import subprocess
import sys
import os
from monitorify import config
from monitorify.ui.tui.tui import MonitorifyApp
import argparse

def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Monitorify")
    parser.add_argument("--ip", type=str, default=None, help="IP address of the remote machine")
    parser.add_argument("--port", type=int, default=None, help="Port of the remote machine (default: 22)")
    parser.add_argument("--username", type=str, default=None, help="Username for the remote machine")
    parser.add_argument("--password", type=str, default=None, help="Password for the remote machine")
    parser.add_argument("--key_filename", type=str, default=None, help="Path to the key file for the remote machine")
    args = parser.parse_args()

    if not args.ip and (args.port is not None or args.username or args.password or args.key_filename):
        parser.error("--ip is required when specifying remote connection arguments")

    return args


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
    """Main CLI entrypoint"""
    args = parse_args()

    if args.ip:
        from monitorify.remote.connector import RemoteConnector

        try:
            connector = RemoteConnector(
                host=args.ip,
                port=args.port or 22,
                username=args.username,
                password=args.password,
                key_filename=args.key_filename,
            )
            client = connector.connect()
            try:
                if not args.command and not connector.is_installed(client):
                    print(f"Error: Monitorify is not installed on the remote host ({args.ip}).")
                    response = input("Do you want to install it? (y/n): ").strip().lower()
                    if response == "y":
                        success = connector.install(client)
                        if not success:
                            print("Installation failed.")
                            sys.exit(1)
                    else:
                        sys.exit(1)

                remote_cmd = args.command or "bash -l -c 'monitorify || python3 -m monitorify'"
                connector.run_interactive(client, command=remote_cmd)
            finally:
                client.close()
        except ConnectionError as e:
            print(f"Connection failed: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            pass
        return

    # Local mode
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
