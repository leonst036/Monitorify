# Monitorify

A lightweight system monitor that runs right in your terminal. It tracks CPU usage, memory consumption, network activity, disk metrics, and process states in real time with historical graphing — no bloated dependencies, just a clean, high-performance TUI dashboard.

Built with Python and [Textual](https://github.com/Textualize/textual). Reads directly from `/proc` and `/sys` for lightning-fast, native performance on Linux.

---

## Features

* **CPU & System Info** — Live CPU percentage, multi-timeframe braille graphing, OS kernel, hostname, and system uptime.
* **Memory (RAM)** — Real-time memory utilization, percentage, and historical graph.
* **Network Throughput** — Split-view upload/download graph with current speed, peak throughput, and total transferred bytes.
* **Disk Metrics** — I/O activity rates (reads/writes) and storage capacity breakdown for physical disks.
* **Process Monitor** — Interactive list of running processes with CPU/RAM metrics, process state, uptime, and real-time inspector.
* **Background Collector Daemon** — Lightweight collector logging metrics to an SQLite database (`~/.local/share/monitorify/monitorify.db`) with automatic pruning.
* **Customizable Menu (`m`)** — Toggle widget visibility, adjust collection frequency, and set history graph duration (1m, 5m, 10m, 30m, 1h, or custom durations like `2h`, `1d`).

---

## Installation

### Method 1: Using `pipx` (Recommended for Linux CLI tools)

[pipx](https://pypa.github.io/pipx/) installs Monitorify in an isolated environment and makes the `monitorify` command globally available:

```bash
# Install directly from GitHub
pipx install git+https://github.com/leonst036/Monitorify.git

# Or if published on PyPI
pipx install monitorify
```

To update later:
```bash
pipx upgrade monitorify
```

*(You can also use `uv tool install git+https://github.com/leonst036/Monitorify.git`)*

---

### Method 2: Development / From Source

```bash
# Clone the repository
git clone https://github.com/leonst036/Monitorify.git
cd Monitorify

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .
```

---

## Usage

### Run the Dashboard

```bash
monitorify
```

* Press **`m`** to open the settings menu (toggle widgets, set intervals, change history window).
* Press **`q`** or **`c`** to quit.

---

### Standalone Background Collector Daemon

Monitorify includes a background collector daemon that records metrics continuously to SQLite:

```bash
monitorify-daemon
```

#### Optional: 24/7 Always-On Service (systemd user service)

To collect system metrics 24/7 in the background even when the dashboard is closed, create `~/.config/systemd/user/monitorify.service`:

```ini
[Unit]
Description=Monitorify Metrics Collector Daemon

[Service]
ExecStart=%h/.local/bin/monitorify-daemon
Restart=always

[Install]
WantedBy=default.target
```

Enable and start it with:
```bash
systemctl --user daemon-reload
systemctl --user enable --now monitorify
```

---

## Configuration & Paths

Monitorify adheres to standard Linux XDG base directories:

| Purpose | Default Path | Environment Variable |
|---|---|---|
| **Database** | `~/.local/share/monitorify/monitorify.db` | `MONITORIFY_DB_PATH` |
| **Daemon PID** | `/run/user/<uid>/monitorify/daemon.pid` | `MONITORIFY_PID_PATH` |
| **Interval** | `1.0` seconds | `MONITORIFY_INTERVAL` |
| **Retention** | `604800` seconds (7 days) | `MONITORIFY_RETENTION` |

---

## Project Structure

```
Monitorify/
├── pyproject.toml               # Package build configuration & entry points
├── README.md                    # Documentation
├── main.py                      # Developer entrypoint shim
├── src/
│   └── monitorify/
│       ├── __init__.py          # Package metadata (__version__)
│       ├── __main__.py          # python -m monitorify entrypoint
│       ├── config.py            # XDG path handling & environment settings
│       ├── main.py              # Dashboard runner & daemon supervisor
│       ├── daemon.py            # Standalone metrics collector daemon
│       ├── collector/
│       │   ├── manager.py       # Worker lifecycle coordinator
│       │   ├── worker.py        # Background metric collection thread
│       │   └── schema.py        # Dataclass metric structures
│       ├── stats/
│       │   ├── cpuStats.py      # /proc/stat CPU calculator
│       │   ├── ramStats.py      # /proc/meminfo RAM calculator
│       │   ├── networkStats.py  # /proc/net/dev throughput calculator
│       │   ├── DiskStats.py     # /proc/diskstats I/O & storage parser
│       │   └── programmList.py  # /proc process parser & cache thread
│       ├── storage/
│       │   └── db.py            # SQLite metrics storage & historical queries
│       └── ui/
│           └── tui/
│               ├── tui.py       # Main Textual App
│               ├── css/
│               │   └── tui.css  # TUI styling & themes
│               ├── components/
│               │   ├── menu.py          # Settings sidebar component
│               │   └── widgetManager.py # Dynamic grid layout organizer
│               └── widgets/
│                   ├── brailleGraph.py       # High-density Unicode graph
│                   ├── cpuWidget.py          # CPU monitor widget
│                   ├── ramWidget.py          # RAM monitor widget
│                   ├── networkWidget.py      # Network monitor widget
│                   ├── diskWidget.py         # Disk I/O & storage widget
│                   ├── programmListWidget.py # Interactive process list
│                   ├── procInfoWidget.py     # Process details panel
│                   └── statusWidget.py       # Host & kernel status
```

---

## Requirements

* **Python:** 3.10+
* **OS:** Linux (relies on `/proc` and `/sys` filesystems)
* **Terminal:** Minimum 80 columns × 24 lines recommended
