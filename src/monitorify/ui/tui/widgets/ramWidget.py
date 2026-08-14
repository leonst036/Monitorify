# pyrefly: ignore [missing-import]
from textual.widgets import Static
# pyrefly: ignore [missing-import]
from textual.containers import Container
from monitorify.ui.tui.widgets.brailleGraph import BrailleGraph, make_time_grid


class RamWidget(Container):
    BORDER_TITLE = "MEM"

    def compose(self):
        self.ram_usage_static = Static("–%")
        yield self.ram_usage_static

        self.sparkline = BrailleGraph(
            data_lines=1, color1="#c678dd", y_max=100.0,
            show_timeline=True,
            id="ram_sparkline"
        )
        yield self.sparkline

    def update_ram(self, snapshot) -> None:
        """Update label and append one live data point to the graph."""
        usage = snapshot.ram
        self.ram_usage_static.update(f"{usage:.1f}%")
        self.sparkline.update_value(usage)

    def update_text(self, snapshot) -> None:
        """Update only the label — does not touch the graph."""
        self.ram_usage_static.update(f"{snapshot.ram:.1f}%")

    def load_history(self, snapshots: list, time_span: float = 0.0) -> None:
        """Bulk-load RAM history, time-positioned to show real gaps."""
        w = self.sparkline.size.width * 2 or 400
        values = make_time_grid(snapshots, lambda s: s.ram, time_span, w)
        self.sparkline.load_history(values, timeline_seconds=time_span)
