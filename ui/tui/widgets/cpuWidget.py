# pyrefly: ignore [missing-import]
from textual.widgets import Static
# pyrefly: ignore [missing-import]
from textual.containers import Container, Vertical
from stats.cpuStats import get_cpu_usage
from ui.tui.widgets.brailleGraph import BrailleGraph
from ui.tui.widgets.statusWidget import StatusWidget


class CpuWidget(Container):
    BORDER_TITLE = "CPU │ [bold #c678dd]M[/bold #c678dd]enu   [bold #c678dd]Q[/bold #c678dd]uit"

    def compose(self):
        self.cpu_usage_static = Static(f"{get_cpu_usage(unit='percent')}%")
        yield self.cpu_usage_static

        # Initialize the reusable graph widget
        self.sparkline = BrailleGraph(data_lines=1, color1="#61afef", y_max=100.0, id="cpu_sparkline")
        yield self.sparkline

    def on_mount(self):
        self.status_box = StatusWidget(id="status_box")
        # Mount to screen so it has absolutely ZERO effect on CpuWidget's internal layout
        self.screen.mount(self.status_box)

    def on_resize(self):
        if hasattr(self, "status_box"):
            box_width = 30  # matches CSS width
            # Position relative to screen coordinates
            self.status_box.styles.offset = (self.region.x + self.size.width - box_width, self.region.y)

    def update_cpu(self):
        usage = get_cpu_usage(unit='percent')
        self.cpu_usage_static.update(f"{usage}%")
        
        # Update graph data through the helper method
        self.sparkline.update_value(usage)