# pyrefly: ignore [missing-import]
from textual.widgets import Static
# pyrefly: ignore [missing-import]
from textual.containers import Container
from stats.ramStats import get_ram_usage
from ui.tui.widgets.brailleGraph import BrailleGraph


class RamWidget(Container):
    BORDER_TITLE = "MEM"

    def compose(self):
        self.ram_usage_static = Static(f"{get_ram_usage(unit='percent')}%")
        yield self.ram_usage_static

        # Initialize the reusable graph widget
        self.sparkline = BrailleGraph(data_lines=1, color1="#c678dd", y_max=100.0, id="ram_sparkline")
        yield self.sparkline

    def update_ram(self):
        usage = get_ram_usage(unit='percent')
        self.ram_usage_static.update(f"{usage}%")
        
        # Update graph data through the helper method
        self.sparkline.update_value(usage)
