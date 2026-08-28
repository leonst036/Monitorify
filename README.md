# Monitorify
### A terminal montioring tool for linux

- Features
- CPU monitoring 
- RAM monitoring
- Network monitoring
- Disk monitoring (I/O and storage capacity)
- Process monitoring
- Background daemon
- Customization menu (toggle widgets, set intervals, and change history window)
- Historical graphs

## Requirements

* **Python:** 3.10+
* **OS:** Linux (relies on `/proc` and `/sys` filesystems)
* **Terminal:** Minimum 80 columns × 24 lines recommended

## Installation
### Using pipx
```bash
pipx install git+https://github.com/leonst036/Monitorify.git
```
Or from PyPI:
```bash
pipx install monitorify
```

### Using pip
```bash
pip install git+https://github.com/leonst036/Monitorify.git
```

### Using source
```bash
git clone https://github.com/leonst036/Monitorify.git
cd Monitorify
pip install . 
```

## Usage
```bash
monitorify
```

## Background Daemon

The daemon collects metrics continuously to SQLite, even when the dashboard is closed.

### Manually (foreground)

```bash
monitorify-daemon
```

### Always-On via systemd --user

Create the service file at `~/.config/systemd/user/monitorify.service`:

```ini
[Unit]
Description=Monitorify Metrics Collector Daemon

[Service]
ExecStart=%h/.local/bin/monitorify-daemon
Restart=always

[Install]
WantedBy=default.target
```

Enable and start it:

```bash
systemctl --user daemon-reload
systemctl --user enable --now monitorify
```

Check status or logs:

```bash
systemctl --user status monitorify
journalctl --user -u monitorify -f
```

Stop or disable:

```bash
systemctl --user stop monitorify
systemctl --user disable monitorify
```

## File Locations

Monitorify follows XDG Base Directory conventions — nothing is written to the install directory.

| Purpose | Default Path | Override |
|---|---|---|
| **Database** | `~/.local/share/monitorify/monitorify.db` | `MONITORIFY_DB_PATH` env var |
| **Daemon PID** | `/run/user/<uid>/monitorify/daemon.pid` | `MONITORIFY_PID_PATH` env var |
| **Collection interval** | `1.0` seconds | `MONITORIFY_INTERVAL` env var |
| **Data retention** | `604800` s (7 days) | `MONITORIFY_RETENTION` env var |

## Remote

To use Monitorify remotely over SSH on your server, you can set the following parameters:

- `--ip` – Set the target IP address.
- `--port` – Set the SSH port.
- `--username` – Set the username for the remote host.
- `--password` – Set the password for the SSH server.
- `--key_filename` – Set the path to an SSH key *(optional)*.

## Tech Stack

* **Language & TUI:** Python, Textual
* **Database:** SQLite
* **Target OS:** Linux

## Uninstalling

```bash
# If installed via pipx
pipx uninstall monitorify

# Remove stored data
rm -rf ~/.local/share/monitorify
rm -rf /run/user/$(id -u)/monitorify
```