# pyrefly: ignore [missing-import]
from textual.widgets import Static
# pyrefly: ignore [missing-import]
from textual.containers import Container, Vertical
from ui.tui.widgets.brailleGraph import BrailleGraph, make_time_grid
from ui.tui.widgets.statusWidget import StatusWidget


class CpuWidget(Container):
    BORDER_TITLE = "CPU │ [bold #c678dd]M[/bold #c678dd]enu   [bold #c678dd]Q[/bold #c678dd]uit"

    def compose(self):
        self.cpu_usage_static = Static("–%")
        yield self.cpu_usage_static

        self.sparkline = BrailleGraph(
            data_lines=1, color1="#61afef", y_max=100.0,
            show_timeline=True,
            id="cpu_sparkline"
        )
        yield self.sparkline

    def on_mount(self):
        self.status_box = StatusWidget(id="status_box")
        self.screen.mount(self.status_box)

    def on_resize(self):
        if hasattr(self, "status_box"):
            box_width = 30
            self.status_box.styles.offset = (self.region.x + self.size.width - box_width, self.region.y)

    def update_cpu(self, snapshot) -> None:
        """Update label and append one live data point to the graph."""
        usage = snapshot.cpu
        self.cpu_usage_static.update(f"{usage:.1f}%")
        self.sparkline.update_value(usage)

    def update_text(self, snapshot) -> None:
        """Update only the label — does not touch the graph."""
        self.cpu_usage_static.update(f"{snapshot.cpu:.1f}%")

    def load_history(self, snapshots: list, time_span: float = 0.0) -> None:
        """Bulk-load CPU history, time-positioned to show real gaps."""
        w = self.sparkline.size.width * 2 or 400
        values = make_time_grid(snapshots, lambda s: s.cpu, time_span, w)
        self.sparkline.load_history(values, timeline_seconds=time_span)