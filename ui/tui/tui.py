import sys
from pathlib import Path

# Add project root to sys.path if running script directly
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# pyrefly: ignore [missing-import]
from textual.app import App, ComposeResult
# pyrefly: ignore [missing-import]
from textual.widgets import Header, Footer
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
        yield CpuWidget()
        yield RamWidget()
        yield NetworkWidget()

    def on_mount(self) -> None:

        self.set_interval(1.0, self.update_display)

    def update_display(self) -> None:
        self.query_one(CpuWidget).update_cpu()
        self.query_one(RamWidget).update_ram()
        self.query_one(NetworkWidget).update_network()


if __name__ == "__main__":
    app = MonitorifyApp()
    app.run()