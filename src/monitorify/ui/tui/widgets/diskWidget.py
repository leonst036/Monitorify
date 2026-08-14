# pyrefly: ignore [missing-import]
from textual.widgets import Static
# pyrefly: ignore [missing-import]
from textual.containers import Container, Vertical
from monitorify.ui.tui.widgets.brailleGraph import BrailleGraph, make_time_grid


def format_bps(bps: float) -> str:
    if bps >= 1024 * 1024 * 1024:
        return f"{bps / (1024 ** 3):.1f} GB/s"
    elif bps >= 1024 * 1024:
        return f"{bps / (1024 * 1024):.1f} MB/s"
    elif bps >= 1024:
        return f"{bps / 1024:.1f} KB/s"
    else:
        return f"{bps:.0f} B/s"


def format_bytes(b: float) -> str:
    if b >= 1024 ** 4:
        return f"{b / (1024 ** 4):.1f} TB"
    elif b >= 1024 ** 3:
        return f"{b / (1024 ** 3):.1f} GB"
    elif b >= 1024 ** 2:
        return f"{b / (1024 ** 2):.1f} MB"
    elif b >= 1024:
        return f"{b / 1024:.1f} KB"
    else:
        return f"{b:.0f} B"


def format_storage_summary(disk_storage: dict | None) -> str:
    if not disk_storage or not isinstance(disk_storage, dict):
        return "Storage: –"

    total = sum(d.get("total", 0) for d in disk_storage.values() if isinstance(d, dict))
    used = sum(d.get("used", 0) for d in disk_storage.values() if isinstance(d, dict))
    pct = (used / total * 100) if total > 0 else 0
    return f"{format_bytes(used)}/{format_bytes(total)} ({pct:.0f}%)"


class DiskRatePoint:
    def __init__(self, timestamp: float, read_bps: float, write_bps: float):
        self.timestamp = timestamp
        self.read_bps = read_bps
        self.write_bps = write_bps


def compute_disk_rates(snapshots: list) -> list[DiskRatePoint]:
    points = []
    prev_ts = None
    prev_read = None
    prev_write = None

    for s in snapshots:
        if s.disk_io is None or not isinstance(s.disk_io, dict):
            prev_ts = None
            continue

        curr_read = sum(d.get("read_bytes", 0) for d in s.disk_io.values() if isinstance(d, dict))
        curr_write = sum(d.get("write_bytes", 0) for d in s.disk_io.values() if isinstance(d, dict))

        if prev_ts is not None:
            dt = s.timestamp - prev_ts
            if 0 < dt <= 10.0:
                r_bps = max(0.0, curr_read - prev_read) / dt
                w_bps = max(0.0, curr_write - prev_write) / dt
                points.append(DiskRatePoint(s.timestamp, r_bps, w_bps))
            else:
                points.append(DiskRatePoint(s.timestamp, 0.0, 0.0))
        else:
            points.append(DiskRatePoint(s.timestamp, 0.0, 0.0))

        prev_ts = s.timestamp
        prev_read = curr_read
        prev_write = curr_write

    return points


class DiskInfo(Container):
    def compose(self):
        self.write_current = Static("▲ 0 B/s", classes="tx_text")
        self.write_top = Static("▲ Top: 0 B/s", classes="tx_text")

        self.read_current = Static("▼ 0 B/s", classes="rx_text")
        self.read_top = Static("▼ Top: 0 B/s", classes="rx_text")

        self.storage_label = Static("Storage: –", classes="storage_text")

        yield self.write_current
        yield self.write_top
        yield Static("")  # Spacer
        yield self.read_current
        yield self.read_top
        yield Static("")  # Spacer
        yield self.storage_label


class DiskWidget(Container):
    BORDER_TITLE = "DISK"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.top_read: float = 0.0
        self.top_write: float = 0.0
        self.current_read: float = 0.0
        self.current_write: float = 0.0
        self.last_timestamp: float | None = None
        self.last_read_bytes: float = 0.0
        self.last_write_bytes: float = 0.0

    def compose(self):
        self.disk_graph = BrailleGraph(
            data_lines=2,
            color1="#c678dd",
            color2="#61afef",
            show_scale=True,
            scale_fmt=format_bps,
            show_timeline=True,
            id="disk_graph",
        )
        yield self.disk_graph

        with Vertical(id="disk_info_wrapper"):
            self.disk_info = DiskInfo(id="disk_info")
            self.disk_info.border_title = "write"
            self.disk_info.border_subtitle = "read"
            yield self.disk_info

    def _calculate_rates(self, snapshot) -> tuple[float, float]:
        if snapshot.disk_io is None or not isinstance(snapshot.disk_io, dict):
            return 0.0, 0.0

        total_read = sum(d.get("read_bytes", 0) for d in snapshot.disk_io.values() if isinstance(d, dict))
        total_write = sum(d.get("write_bytes", 0) for d in snapshot.disk_io.values() if isinstance(d, dict))

        if self.last_timestamp is None:
            self.last_timestamp = snapshot.timestamp
            self.last_read_bytes = total_read
            self.last_write_bytes = total_write
            return 0.0, 0.0

        if snapshot.timestamp <= self.last_timestamp:
            return self.current_read, self.current_write

        dt = snapshot.timestamp - self.last_timestamp
        if 0 < dt <= 10.0:
            read_bps = max(0.0, total_read - self.last_read_bytes) / dt
            write_bps = max(0.0, total_write - self.last_write_bytes) / dt
        else:
            read_bps = 0.0
            write_bps = 0.0

        self.last_timestamp = snapshot.timestamp
        self.last_read_bytes = total_read
        self.last_write_bytes = total_write
        self.current_read = read_bps
        self.current_write = write_bps

        return read_bps, write_bps

    def update_disk(self, snapshot) -> None:
        """Update labels and append one live data point to the graph."""
        read_bps, write_bps = self._calculate_rates(snapshot)
        self.top_read = max(self.top_read, read_bps)
        self.top_write = max(self.top_write, write_bps)
        self._refresh_labels(read_bps, write_bps, snapshot.disk_storage)
        self.disk_graph.update_value(write_bps, read_bps)

    def update_labels(self, snapshot) -> None:
        """Update only the text labels — does not touch the graph."""
        read_bps, write_bps = self._calculate_rates(snapshot)
        self.top_read = max(self.top_read, read_bps)
        self.top_write = max(self.top_write, write_bps)
        self._refresh_labels(read_bps, write_bps, snapshot.disk_storage)

    def _refresh_labels(self, read_bps: float, write_bps: float, disk_storage: dict | None) -> None:
        info = self.disk_info
        info.write_current.update(f"▲ {format_bps(write_bps)}")
        info.write_top.update(f"▲ Top: {format_bps(self.top_write)}")
        info.read_current.update(f"▼ {format_bps(read_bps)}")
        info.read_top.update(f"▼ Top: {format_bps(self.top_read)}")
        info.storage_label.update(format_storage_summary(disk_storage))

    def load_history(self, snapshots: list, time_span: float = 0.0) -> None:
        """Bulk-load disk I/O history, time-positioned to show real gaps."""
        w = self.disk_graph.size.width * 2 or 400
        rate_points = compute_disk_rates(snapshots)
        read_vals = make_time_grid(rate_points, lambda p: p.read_bps, time_span, w)
        write_vals = make_time_grid(rate_points, lambda p: p.write_bps, time_span, w)

        real_read = [v for v in read_vals if v is not None]
        real_write = [v for v in write_vals if v is not None]
        if real_read:
            self.top_read = max(real_read)
        if real_write:
            self.top_write = max(real_write)

        if snapshots:
            last = snapshots[-1]
            if last.disk_io and isinstance(last.disk_io, dict):
                self.last_timestamp = last.timestamp
                self.last_read_bytes = sum(d.get("read_bytes", 0) for d in last.disk_io.values() if isinstance(d, dict))
                self.last_write_bytes = sum(d.get("write_bytes", 0) for d in last.disk_io.values() if isinstance(d, dict))

        self.disk_graph.load_history(write_vals, read_vals, timeline_seconds=time_span)
