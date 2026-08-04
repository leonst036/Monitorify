# Monitorify

A lightweight system monitor that runs right in your terminal. It tracks CPU usage, memory consumption, and network activity in real time — no GUI needed, no bloated dependencies, just a clean TUI dashboard you can glance at whenever you want.

Built with Python and [Textual](https://github.com/Textualize/textual). Reads directly from `/proc`, so it stays fast and dependency-light on Linux.

## What it looks like

When you fire it up, you'll see a grid layout with:

- **CPU** — current usage percentage with a live braille-character graph scrolling across the panel
- **MEM** — same deal, but for RAM
- **NET** — download and upload speeds graphed in a split view (download on top, upload on bottom), plus a sidebar showing current speed, peak speed, and total bytes transferred

The graphs use Unicode braille characters to squeeze a surprising amount of detail into a small terminal window. If your terminal gets too small (below 80×24), it'll show a friendly resize warning instead of a broken layout.

## Getting started

You'll need Python 3.10+ and a Linux system (since it reads from `/proc/stat`, `/proc/meminfo`, and `/proc/net/dev`).

```bash
# Clone the repo
git clone https://github.com/leonst036/Monitorify.git
cd Monitorify

# Set up a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run it
python main.py
```

Press `q` or `c` to quit.

## How it works

The app pulls system stats by reading proc files directly — no shelling out, no `psutil`. Each metric has its own module under `stats/`:

- `cpuStats.py` — parses `/proc/stat` to calculate CPU usage between snapshots
- `ramStats.py` — reads `/proc/meminfo` for available vs. total memory
- `networkStats.py` — reads `/proc/net/dev` to compute bytes per second for upload and download

The TUI side lives under `ui/tui/` and is built on Textual. Each stat gets its own widget (`cpuWidget`, `ramWidget`, `networkWidget`), and they all share a custom `BrailleGraph` widget that renders scrolling graphs using braille dot patterns. The main app refreshes everything once per second.

## Project structure

```
Monitorify/
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── stats/
│   ├── cpuStats.py          # CPU usage from /proc/stat
│   ├── ramStats.py          # RAM usage from /proc/meminfo
│   └── networkStats.py      # Network throughput from /proc/net/dev
└── ui/
    └── tui/
        ├── tui.py           # Main Textual app
        ├── css/
        │   └── tui.css      # Layout and styling
        └── widgets/
            ├── cpuWidget.py      # CPU display widget
            ├── ramWidget.py      # RAM display widget
            ├── networkWidget.py  # Network display widget
            └── brailleGraph.py   # Braille-character graphing widget
```

## Requirements

- **Python** 3.10+
- **Linux** (relies on `/proc` filesystem)
- **Terminal** at least 80 columns wide and 24 lines tall
