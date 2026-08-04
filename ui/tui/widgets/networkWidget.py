# pyrefly: ignore [missing-import]
from textual.widgets import Static
from textual.containers import Container
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

class NetworkWidget(Container):
    BORDER_TITLE = "NET"

    def compose(self):
        self.network_usage_static = Static("Init...")
        yield self.network_usage_static

        self.total_network_usage_static = Static("Init...")
        yield self.total_network_usage_static
        
        # data_lines=2 creates the mirrored graph for download/upload
        self.network_graph = BrailleGraph(data_lines=2, color1="#61afef", color2="#c678dd", id="network_graph")
        yield self.network_graph

    def update_network(self):
        rx_bps, tx_bps = get_network_usage()
        
        rx_str = format_bps(rx_bps)
        tx_str = format_bps(tx_bps)
        
        self.network_usage_static.update(f"↓ {rx_str}  ↑ {tx_str}")
        
        total_rx, total_tx = get_total_network_stats()
        self.total_network_usage_static.update(f"{format_bytes(total_rx)} ↓  {format_bytes(total_tx)} ↑")
        
        self.network_graph.update_value(rx_bps, tx_bps)
