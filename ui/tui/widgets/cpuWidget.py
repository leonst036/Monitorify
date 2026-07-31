# pyrefly: ignore [missing-import]
from textual.widgets import Static
# pyrefly: ignore [missing-import]
from textual.containers import Container
from stats.cpuStats import get_cpu_usage
from ui.tui.widgets.historySparkline import HistorySparkline


class CpuWidget(Container):
    def compose(self):
        yield Static("CPU Usage")
        
        self.cpu_usage_static = Static(f"{get_cpu_usage(unit='percent')}%")
        yield self.cpu_usage_static

        # Initialize the reusable graph widget
        self.sparkline = HistorySparkline(max_points=50, summary_function=max)
        yield self.sparkline

    def update_cpu(self):
        usage = get_cpu_usage(unit='percent')
        self.cpu_usage_static.update(f"{usage}%")
        
        # Update graph data through the helper method
        self.sparkline.update_value(usage)