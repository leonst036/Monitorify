# pyrefly: ignore [missing-import]
from textual.widgets import Static
from textual.containers import Container, Vertical
from stats.networkStats import get_network_usage, get_total_network_stats
from ui.tui.widgets.brailleGraph import BrailleGraph

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
        self.rx_total = Static("▼ Total: 0 B", classes="rx_text")
        
        self.tx_current = Static("▲ 0 B/s", classes="tx_text")
        self.tx_top = Static("▲ Top: 0 B/s", classes="tx_text")
        self.tx_total = Static("▲ Total: 0 B", classes="tx_text")
        
        yield self.rx_current
        yield self.rx_top
        yield self.rx_total
        yield Static("") # Spacer
        yield self.tx_current
        yield self.tx_top
        yield self.tx_total


class NetworkWidget(Container):
    BORDER_TITLE = "NET"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.top_rx = 0
        self.top_tx = 0

    def compose(self):
        self.network_graph = BrailleGraph(data_lines=2, color1="#61afef", color2="#c678dd", id="network_graph")
        yield self.network_graph
        
        with Vertical(id="network_info_wrapper"):
            self.network_info = NetworkInfo(id="network_info")
            self.network_info.border_title = "download"
            self.network_info.border_subtitle = "upload"
            yield self.network_info

    def update_network(self):
        rx_bps, tx_bps = get_network_usage()
        
        self.top_rx = max(self.top_rx, rx_bps)
        self.top_tx = max(self.top_tx, tx_bps)
        
        info = self.network_info
        info.rx_current.update(f"▼ {format_bps(rx_bps)}")
        info.rx_top.update(f"▼ Top: {format_bps(self.top_rx)}")
        
        info.tx_current.update(f"▲ {format_bps(tx_bps)}")
        info.tx_top.update(f"▲ Top: {format_bps(self.top_tx)}")
        
        total_rx, total_tx = get_total_network_stats()
        info.rx_total.update(f"▼ Total: {format_bytes(total_rx)}")
        info.tx_total.update(f"▲ Total: {format_bytes(total_tx)}")
        
        self.network_graph.update_value(rx_bps, tx_bps)
