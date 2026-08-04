import sys
from pathlib import Path

# Add project root to sys.path if running script directly
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# pyrefly: ignore [missing-import]
from textual.app import App, ComposeResult
# pyrefly: ignore [missing-import]
from textual.widgets import Header, Footer, Label
from textual.containers import Container, Center, Middle
from ui.tui.widgets.cpuWidget import CpuWidget
from ui.tui.widgets.ramWidget import RamWidget
from ui.tui.widgets.networkWidget import NetworkWidget


class MonitorifyApp(App):
    CSS_PATH = "css/tui.css"

    TITLE = "Monitorify"
    BINDINGS = [
        ("q", "quit"),
        ("c", "quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="main_container"):
            yield CpuWidget()
            yield RamWidget()
            yield NetworkWidget()
        with Center(id="warning_container"):
            with Middle():
                yield Label("Terminal window is too small!\nPlease resize.", id="warning_label")

    def on_mount(self) -> None:
        self.action_get_window_size()
        self.set_interval(1.0, self.update_display)

    def update_display(self) -> None:
        self.action_get_window_size()
        
        if self.query_one("#main_container").display:
            self.query_one(CpuWidget).update_cpu()
            self.query_one(RamWidget).update_ram()
            self.query_one(NetworkWidget).update_network()
    
    def action_get_window_size(self) -> None:
        is_too_small = self.size.width < 80 or self.size.height < 24
        
        if is_too_small:
            self.query_one("#main_container").display = False
            self.query_one("#warning_container").display = True
        else:
            self.query_one("#main_container").display = True
            self.query_one("#warning_container").display = False
if __name__ == "__main__":
    app = MonitorifyApp()
    app.run()