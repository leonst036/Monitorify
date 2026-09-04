import getpass
import os
from typing import Optional
from monitorify.storage.db import Database


def add_remote(
    ip: Optional[str] = None,
    port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    key_filename: Optional[str] = None,
    db: Optional[Database] = None,
) -> int:
    """Prompt for remote host details if not provided, and save to database."""
    if not ip:
        ip = input("Enter IP address: ").strip()
    if not ip:
        print("Error: IP address cannot be empty.")
        return -1

    if port is None:
        port_input = input("Enter port (default 22): ").strip()
        port = int(port_input) if port_input.isdigit() else 22
    elif isinstance(port, str):
        port = int(port) if port.isdigit() else 22

    if not (1 <= port <= 65535):
        port = 22

    if username is None:
        username_input = input("Enter username (default root): ").strip()
        username = username_input if username_input else "root"
    else:
        username = username.strip() or "root"

    if password is None and key_filename is None:
        password_input = getpass.getpass("Enter password (leave blank to use SSH keys): ").strip()
        if password_input:
            password = password_input
            key_filename = None
        else:
            password = None
            key_input = input("Enter key filename: ").strip()
            key_filename = key_input if key_input else None
    else:
        password = password if password else None
        key_filename = key_filename if key_filename else None

    if key_filename:
        key_filename = os.path.expanduser(key_filename)

    close_db = False
    if db is None:
        db = Database()
        close_db = True

    try:
        host_id = db.save_host(
            ip=ip,
            port=port,
            username=username,
            password=password,
            key_filename=key_filename,
        )
        if host_id != -1:
            print(f"Host '{username}@{ip}:{port}' saved to database (ID: {host_id}).")
        else:
            print("Failed to save host to database.")
        return host_id
    finally:
        if close_db:
            db.disconnect()


def list_hosts(db: Optional[Database] = None) -> list[dict]:
    """List all saved remote hosts."""
    close_db = False
    if db is None:
        db = Database()
        close_db = True

    try:
        hosts = db.get_hosts()
        if not hosts:
            print("No saved hosts found.")
            return []

        print(f"{'ID':<5} {'Host':<35} {'Auth':<20}")
        print("-" * 65)
        for h in hosts:
            host_str = f"{h['username']}@{h['ip']}:{h['port']}"
            auth_str = f"Key: {h['key_filename']}" if h['key_filename'] else ("Password: ***" if h['password'] else "None")
            print(f"{h['id']:<5} {host_str:<35} {auth_str:<20}")
        return hosts
    finally:
        if close_db:
            db.disconnect()


def remove_host(host_id: Optional[int] = None, db: Optional[Database] = None) -> bool:
    """Remove a saved remote host by ID."""
    close_db = False
    if db is None:
        db = Database()
        close_db = True

    try:
        if host_id is None:
            hosts = db.get_hosts()
            if not hosts:
                print("No saved hosts to remove.")
                return False
            list_hosts(db=db)
            id_input = input("Enter host ID to remove: ").strip()
            if not id_input.isdigit():
                print("Invalid host ID.")
                return False
            host_id = int(id_input)

        if db.delete_host(host_id):
            print(f"Host ID {host_id} successfully deleted.")
            return True
        else:
            print(f"Failed to delete host ID {host_id}.")
            return False
    finally:
        if close_db:
            db.disconnect()


def handle_host_action(action: str, args=None) -> None:
    """Handle --host subcommands."""
    action = (action or "").lower()
    if action == "add":
        ip = getattr(args, "ip", None)
        port = getattr(args, "port", None)
        username = getattr(args, "username", None)
        password = getattr(args, "password", None)
        key_filename = getattr(args, "key_filename", None)
        add_remote(
            ip=ip,
            port=port,
            username=username,
            password=password,
            key_filename=key_filename,
        )
    elif action == "list":
        list_hosts()
    elif action in ("remove", "delete"):
        remove_host()
    else:
        print(f"Unknown host action: '{action}'. Supported actions: add, list, remove")


if __name__ == "__main__":
    add_remote()