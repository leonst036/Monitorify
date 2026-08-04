# pyrefly: ignore [missing-import]
from textual.widgets import Static
from textual.containers import Container
from stats.networkStats import get_network_usage
from ui.tui.widgets.brailleGraph import BrailleGraph

def format_bps(bps):
    if bps >= 1024 * 1024:
        return f"{bps / (1024 * 1024):.1f} MB/s"
    elif bps >= 1024:
        return f"{bps / 1024:.1f} KB/s"
    else:
        return f"{bps:.0f} B/s"

class NetworkWidget(Container):
    BORDER_TITLE = "NET"

    def compose(self):
        self.network_usage_static = Static("Init...")
        yield self.network_usage_static

        # data_lines=2 creates the mirrored graph for download/upload
        self.network_graph = BrailleGraph(data_lines=2, color1="#61afef", color2="#c678dd", id="network_graph")
        yield self.network_graph

    def update_network(self):
        rx_bps, tx_bps = get_network_usage()
        
        rx_str = format_bps(rx_bps)
        tx_str = format_bps(tx_bps)
        
        self.network_usage_static.update(f"↓ {rx_str}  ↑ {tx_str}")
        self.network_graph.update_value(rx_bps, tx_bps)
