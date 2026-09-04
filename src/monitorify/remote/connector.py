import os
import paramiko


class RemoteConnector:
    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str | None = None,
        password: str | None = None,
        key_filename: str | None = None,
        timeout: float = 10.0,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = os.path.expanduser(key_filename) if key_filename else None
        self.timeout = timeout

    def connect(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                key_filename=self.key_filename,
                timeout=self.timeout,
            )
        except paramiko.AuthenticationException as e:
            raise ConnectionError(f"Authentication failed: {e}")
        except paramiko.SSHException as e:
            raise ConnectionError(f"SSH error: {e}")
        except Exception as e:
            raise ConnectionError(f"Error: {e}")
        return client

    def is_installed(self, client: paramiko.SSHClient) -> bool:
        """Check if monitorify is installed on the remote host."""
        try:
            _, stdout, _ = client.exec_command(
                "bash -l -c 'export PATH=\"$HOME/.local/bin:$PATH\"; command -v monitorify >/dev/null 2>&1 || [ -x \"$HOME/.local/bin/monitorify\" ] || python3 -c \"import monitorify\" >/dev/null 2>&1'"
            )
            return stdout.channel.recv_exit_status() == 0
        except Exception:
            return False

    def install(self, client: paramiko.SSHClient) -> bool:
        """Install monitorify on the remote host using install.sh."""
        import shlex
        from pathlib import Path

        script_path = Path(__file__).parent / "install.sh"
        script_content = script_path.read_text(encoding="utf-8")
        install_cmd = f"bash -l -c {shlex.quote(script_content)}"
        self.run_interactive(client, command=install_cmd)
        return self.is_installed(client)

    def run_interactive(self, client: paramiko.SSHClient, command: str = "monitorify") -> None:
        """Run a command interactively on the remote host with a PTY."""
        import select
        import shutil
        import signal
        import sys
        import termios
        import tty

        transport = client.get_transport()
        if transport is None:
            raise ConnectionError("SSH transport is not active")

        channel = transport.open_session()
        cols, rows = shutil.get_terminal_size()
        term = os.environ.get("TERM", "xterm-256color")
        channel.get_pty(term=term, width=cols, height=rows)
        channel.exec_command(command)

        stdin_fd = sys.stdin.fileno()
        stdout_fd = sys.stdout.fileno()
        is_atty = sys.stdin.isatty()
        old_tty = termios.tcgetattr(stdin_fd) if is_atty else None

        def handle_resize(signum, frame):
            w, h = shutil.get_terminal_size()
            try:
                channel.resize_pty(width=w, height=h)
            except Exception:
                pass

        old_winch_handler = None
        try:
            old_winch_handler = signal.signal(signal.SIGWINCH, handle_resize)
        except Exception:
            pass

        try:
            if is_atty:
                tty.setraw(stdin_fd)
            channel.setblocking(0)

            while True:
                r, _, _ = select.select([channel, stdin_fd], [], [])
                if channel in r:
                    try:
                        data = channel.recv(4096)
                        if not data:
                            break
                        os.write(stdout_fd, data)
                    except Exception:
                        break
                if stdin_fd in r:
                    try:
                        user_input = os.read(stdin_fd, 4096)
                        if not user_input:
                            break
                        channel.sendall(user_input)
                    except Exception:
                        break
        finally:
            if old_winch_handler is not None:
                try:
                    signal.signal(signal.SIGWINCH, old_winch_handler)
                except Exception:
                    pass
            if is_atty and old_tty is not None:
                termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_tty)
            channel.close()


def connect_and_run(
    host: str,
    port: int = 22,
    username: str | None = None,
    password: str | None = None,
    key_filename: str | None = None,
    command: str | None = None,
    pause_on_exit: bool = False,
    timeout: float = 10.0,
) -> bool:
    """Connects to a remote host and runs the interactive session."""
    connector = RemoteConnector(
        host=host,
        port=port or 22,
        username=username,
        password=password,
        key_filename=key_filename,
        timeout=timeout,
    )
    try:
        print(f"\nConnecting to {username or 'root'}@{host}:{port or 22}...")
        client = connector.connect()
        try:
            if not command and not connector.is_installed(client):
                print(f"Error: Monitorify is not installed on the remote host ({host}).")
                response = input("Do you want to install it? (y/n): ").strip().lower()
                if response == "y":
                    success = connector.install(client)
                    if not success:
                        print("Installation failed.")
                        if pause_on_exit:
                            input("Press Enter to return...")
                        return False
                else:
                    if pause_on_exit:
                        input("Press Enter to return...")
                    return False

            remote_cmd = command or "bash -l -c 'export PATH=\"$HOME/.local/bin:$PATH\"; monitorify || python3 -m monitorify'"
            connector.run_interactive(client, command=remote_cmd)
            return True
        finally:
            client.close()
    except ConnectionError as e:
        print(f"Connection failed: {e}")
        if pause_on_exit:
            input("Press Enter to return...")
        return False
    except KeyboardInterrupt:
        print("\nSession cancelled.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        if pause_on_exit:
            input("Press Enter to return...")
        return False