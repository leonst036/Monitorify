# pyrefly: ignore [missing-import]
from textual.widgets import Static
# pyrefly: ignore [missing-import]
from textual.containers import Container
from stats.cpuStats import get_cpu_usage
from ui.tui.widgets.brailleGraph import BrailleGraph


class CpuWidget(Container):
    BORDER_TITLE = "CPU"

    def compose(self):
        self.cpu_usage_static = Static(f"{get_cpu_usage(unit='percent')}%")
        yield self.cpu_usage_static

        # Initialize the reusable graph widget
        self.sparkline = BrailleGraph(data_lines=1, color1="#61afef", y_max=100.0, id="cpu_sparkline")
        yield self.sparkline

    def update_cpu(self):
        usage = get_cpu_usage(unit='percent')
        self.cpu_usage_static.update(f"{usage}%")
        
        # Update graph data through the helper method
        self.sparkline.update_value(usage)