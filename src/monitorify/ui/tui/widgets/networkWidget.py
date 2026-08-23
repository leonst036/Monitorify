# pyrefly: ignore [missing-import]
from textual.widgets import Static
# pyrefly: ignore [missing-import]
from textual.containers import Container, Vertical
from monitorify.ui.tui.widgets.brailleGraph import BrailleGraph, make_time_grid


def format_bps(bps):
    if bps >= 1024 * 1024:
        return f"{bps / (1024 * 1024):.1f} MB/s"
    elif bps >= 1024:
        return f"{bps / 1024:.1f} KB/s"
    else:
        return f"{bps:.0f} B/s"

def format_bytes(b):
    if b >= 1024 ** 3:
        return f"{b / (1024 ** 3):.1f} GB"
    elif b >= 1024 ** 2:
        return f"{b / (1024 ** 2):.1f} MB"
    elif b >= 1024:
        return f"{b / 1024:.1f} KB"
    else:
        return f"{b:.0f} B"


class NetworkInfo(Container):
    def compose(self):
        self.rx_current = Static("▼ 0 B/s", classes="rx_text")
        self.rx_top = Static("▼ Top: 0 B/s", classes="rx_text")

        self.tx_current = Static("▲ 0 B/s", classes="tx_text")
        self.tx_top = Static("▲ Top: 0 B/s", classes="tx_text")

        yield self.rx_current
        yield self.rx_top
        yield Static("")  # Spacer
        yield self.tx_current
        yield self.tx_top


class NetworkWidget(Container):
    BORDER_TITLE = "NET"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.top_rx = 0
        self.top_tx = 0

    def compose(self):
        self.network_graph = BrailleGraph(
            data_lines=2, color1="#61afef", color2="#c678dd",
            show_scale=True, scale_fmt=format_bps,
            show_timeline=True,
            id="network_graph"
        )
        yield self.network_graph

        with Vertical(id="network_info_wrapper"):
            self.network_info = NetworkInfo(id="network_info")
            self.network_info.border_title = "download"
            self.network_info.border_subtitle = "upload"
            yield self.network_info

    def update_network(self, snapshot) -> None:
        """Update labels and append one live data point to the graph"""
        rx_bps, tx_bps = snapshot.network
        self.top_rx = max(self.top_rx, rx_bps)
        self.top_tx = max(self.top_tx, tx_bps)
        self._refresh_labels(rx_bps, tx_bps)
        self.network_graph.update_value(rx_bps, tx_bps)

    def update_labels(self, snapshot) -> None:
        """Update only the text labels"""
        rx_bps, tx_bps = snapshot.network
        self.top_rx = max(self.top_rx, rx_bps)
        self.top_tx = max(self.top_tx, tx_bps)
        self._refresh_labels(rx_bps, tx_bps)

    def _refresh_labels(self, rx_bps: float, tx_bps: float) -> None:
        info = self.network_info
        info.rx_current.update(f"▼ {format_bps(rx_bps)}")
        info.rx_top.update(f"▼ Top: {format_bps(self.top_rx)}")
        info.tx_current.update(f"▲ {format_bps(tx_bps)}")
        info.tx_top.update(f"▲ Top: {format_bps(self.top_tx)}")

    def load_history(self, snapshots: list, time_span: float = 0.0) -> None:
        """Bulk-load network history"""
        w = self.network_graph.size.width * 2 or 400
        rx_vals = make_time_grid(snapshots, lambda s: s.network[0], time_span, w)
        tx_vals = make_time_grid(snapshots, lambda s: s.network[1], time_span, w)
        real_rx = [v for v in rx_vals if v is not None]
        real_tx = [v for v in tx_vals if v is not None]
        if real_rx:
            self.top_rx = max(real_rx)
        if real_tx:
            self.top_tx = max(real_tx)
        self.network_graph.load_history(rx_vals, tx_vals, timeline_seconds=time_span)
