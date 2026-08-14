# Installation Guide
# **Only install this on Linux**

> Back to [README.md](README.md)

---

## Requirements

* **Python:** 3.10+
* **OS:** Linux (relies on `/proc` and `/sys` filesystems)
* **Terminal:** Minimum 80 columns × 24 lines recommended

---

## Method 1: `pipx` (Recommended)

[pipx](https://pypa.github.io/pipx/) installs Monitorify in an isolated virtual environment and makes the `monitorify` command globally available — no venv management needed.

```bash
# Install from GitHub
pipx install git+https://github.com/leonst036/Monitorify.git

# Or, once published on PyPI
pipx install monitorify
```

To update later:
```bash
pipx upgrade monitorify
```

> You can also use [uv](https://github.com/astral-sh/uv):
> ```bash
> uv tool install git+https://github.com/leonst036/Monitorify.git
> ```

---

## Method 2: `pip` (inside a virtual environment)

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install from GitHub
pip install git+https://github.com/leonst036/Monitorify.git

# Or from PyPI once published
pip install monitorify
```

---

## Method 3: From Source (Development)

```bash
# Clone the repository
git clone https://github.com/leonst036/Monitorify.git
cd Monitorify

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode (changes to source take effect immediately)
pip install -e .
```

---

## Running the Dashboard

```bash
monitorify
```

---

## Background Daemon

The daemon collects metrics continuously to SQLite, even when the dashboard is closed.

### Manually (foreground)

```bash
monitorify-daemon
```

Press `Ctrl+C` to stop.

### Always-On via `systemd --user` (Recommended for 24/7 collection)

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

---

## File Locations

Monitorify follows [XDG Base Directory](https://specifications.freedesktop.org/basedir-spec/latest/) conventions — nothing is written to the install directory.

| Purpose | Default Path | Override |
|---|---|---|
| **Database** | `~/.local/share/monitorify/monitorify.db` | `MONITORIFY_DB_PATH` env var |
| **Daemon PID** | `/run/user/<uid>/monitorify/daemon.pid` | `MONITORIFY_PID_PATH` env var |
| **Collection interval** | `1.0` seconds | `MONITORIFY_INTERVAL` env var |
| **Data retention** | `604800` s (7 days) | `MONITORIFY_RETENTION` env var |

Example — change the database location:
```bash
export MONITORIFY_DB_PATH="$HOME/custom/path/metrics.db"
monitorify
```

---

## Uninstalling

```bash
# If installed via pipx
pipx uninstall monitorify

# Remove stored data
rm -rf ~/.local/share/monitorify
rm -rf /run/user/$(id -u)/monitorify
```
