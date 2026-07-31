# pyrefly: ignore [missing-import]
from textual.widgets import Static
# pyrefly: ignore [missing-import]
from textual.containers import Container
from stats.ramStats import get_ram_usage
from ui.tui.widgets.historySparkline import HistorySparkline


class RamWidget(Container):
    def compose(self):
        yield Static("Ram Usage")
        
        self.ram_usage_static = Static(f"{get_ram_usage(unit='percent')}%")
        yield self.ram_usage_static

        # Initialize the reusable graph widget
        self.sparkline = HistorySparkline(max_points=50, summary_function=max)
        yield self.sparkline

    def update_ram(self):
        usage = get_ram_usage(unit='percent')
        self.ram_usage_static.update(f"{usage}%")
        
        # Update graph data through the helper method
        self.sparkline.update_value(usage)
