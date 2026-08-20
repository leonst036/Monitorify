# Monitorify

A system monitor that runs right in your terminal. It tracks CPU usage, memory consumption, network activity, disk metrics, and process states in real time with historical graphing.

Built with Python and [Textual](https://github.com/Textualize/textual). Reads from `/proc` and `/sys` for native performance on Linux.

---

## Features

* **CPU & System Info** — Live CPU percentage, OS kernel, hostname, and system uptime.
* **Memory (RAM)** — Real-time memory utilization, percentage, and historical graph.
* **Network Throughput** — Split-view upload/download graph.
* **Disk Metrics** — I/O activity rates (reads/writes) and storage capacity breakdown for physical disks.
* **Process Monitor** — Interactive list of running processes with CPU/RAM metrics
* **Background Collector Daemon** — Collector logging metrics to an SQLite database (`~/.local/share/monitorify/monitorify.db`) with automatic pruning.
* **Customizable Menu (`m`)** — Toggle widget visibility, adjust collection frequency, and set history graph duration.

---

## Quick Start

```bash
# Recommended — isolated install via pipx
pipx install git+https://github.com/leonst036/Monitorify.git

# Then launch the dashboard
monitorify
```

> For full installation options (pip, source, systemd daemon) see **[INSTALL.md](INSTALL.md)**.

---

## Usage

### Dashboard

```bash
monitorify
```

| Key | Action |
|-----|--------|
| `m` | Open settings menu (toggle widgets, set intervals, change history window) |
| `q` / `c` | Quit |

### Standalone Background Daemon

```bash
monitorify-daemon
```

Metrics are written to `~/.local/share/monitorify/monitorify.db` continuously.

---

## Configuration & Paths

Monitorify follows XDG base directory conventions:

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
├── README.md                    # This file
├── INSTALL.md                   
├── main.py                      
├── src/
│   └── monitorify/
│       ├── __init__.py          
│       ├── __main__.py          
│       ├── config.py            
│       ├── main.py              
│       ├── daemon.py            
│       ├── collector/           # Background collector daemon
│       │   ├── manager.py       
│       │   ├── worker.py        
│       │   └── schema.py        
│       ├── stats/               # CPU, RAM, Network, Disk & Process Stats
│       │   ├── cpuStats.py      
│       │   ├── ramStats.py      
│       │   ├── networkStats.py  
│       │   ├── DiskStats.py     
│       │   └── programmList.py  
│       ├── storage/
│       │   └── db.py            # SQLite metrics storage & historical queries
│       └── ui/
│           └── tui/
│               ├── tui.py       # Main Textual App
│               ├── css/
│               │   └── tui.css  # TUI styling & themes
│               ├── components/
│               │   ├── menu.py         
│               │   └── widgetManager.py 
│               └── widgets/     # widgets for tui
│                   ├── brailleGraph.py       
│                   ├── cpuWidget.py          
│                   ├── ramWidget.py         
│                   ├── networkWidget.py     
│                   ├── diskWidget.py         
│                   ├── programmListWidget.py 
│                   ├── procInfoWidget.py     
│                   └── statusWidget.py       
```

---

## Requirements

* **Python:** 3.10+
* **OS:** Linux (relies on `/proc` and `/sys` filesystems)
* **Terminal:** Minimum 80 columns × 24 lines recommended
