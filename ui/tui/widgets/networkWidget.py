# pyrefly: ignore [missing-import]
from textual.widgets import Static
# pyrefly: ignore [missing-import]
from textual.containers import Container
from stats.networkStats import get_network_usage
from ui.tui.widgets.historySparkline import HistorySparkline


def format_bps(bps):
    if bps >= 1024 * 1024:
        return f"{bps / (1024 * 1024):.1f} MB/s"
    elif bps >= 1024:
        return f"{bps / 1024:.1f} KB/s"
    else:
        return f"{bps:.0f} B/s"


class NetworkWidget(Container):
    def compose(self):
        yield Static("Network Usage")
        
        self.network_usage_static = Static("Init...")
        yield self.network_usage_static

        # Initialize the reusable graph widget
        self.sparkline = HistorySparkline(max_points=50, summary_function=max)
        yield self.sparkline

    def update_network(self):
        rx_bps, tx_bps = get_network_usage()
        
        rx_str = format_bps(rx_bps)
        tx_str = format_bps(tx_bps)
        
        self.network_usage_static.update(f"↓ {rx_str}  ↑ {tx_str}")
        
        # Update graph data through the helper method
        self.sparkline.update_value(rx_bps + tx_bps)
