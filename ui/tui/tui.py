import time
import sys
from pathlib import Path

# Add project root to sys.path if running script directly
project_root = Path(__file__).resolve().parents[3]
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
from ui.tui.widgets.diskWidget import DiskWidget
from ui.tui.components.menu import Menu
from ui.tui.components.widgetManager import WidgetManager
from ui.tui.widgets.programmListWidget import ProgrammListWidget
from storage import Database
import config


class MonitorifyApp(App):
    CSS_PATH = "css/tui.css"

    TITLE = "Monitorify"
    BINDINGS = [
        ("q", "quit"),
        ("c", "quit"),
        ("m", "menu")
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Read-only DB connection — data is written by the daemon
        self.db = Database(config.DB_PATH)
        self.db.connect()
        # Default history window: 1 minute
        self.history_duration: float = 60.0
        # Tracks when graphs were last refreshed (for long-window throttling)
        self._last_graph_refresh: float = 0.0

    def compose(self) -> ComposeResult:
        with Container(id="main_container"):
            yield CpuWidget(id="cpu_widget")
            yield RamWidget(id="ram_widget")
            yield ProgrammListWidget(id="programmList_widget")
            yield NetworkWidget(id="network_widget")
            yield DiskWidget(id="disk_widget")
        yield Menu()
        with Center(id="warning_container"):
            with Middle():
                yield Label("Terminal window is too small!\nPlease resize.", id="warning_label")

    def on_mount(self) -> None:
        self.action_get_window_size()
        self.widget_manager = WidgetManager(self.query_one("#main_container"))
        self.update_layout()
        self.update_interval = 1.0
        # Load history from DB on startup
        self.call_after_refresh(self._load_initial_history)
        self.update_timer = self.set_interval(self.update_interval, self.update_display)

    def _load_initial_history(self) -> None:
        """Load history from DB after the first render so widgets have their sizes."""
        self.set_history_duration(self.history_duration)

    def set_update_interval(self, seconds: float) -> None:
        """Updates the graph refresh interval."""
        self.update_interval = seconds
        if hasattr(self, "update_timer") and self.update_timer:
            self.update_timer.stop()
        self.update_timer = self.set_interval(self.update_interval, self.update_display)

    def set_history_duration(self, seconds: float) -> None:
        """Load historical metrics from DB and push them into all graph widgets."""
        self.history_duration = seconds
        start_time = time.time() - seconds
        snapshots = self.db.get_history(limit=10000, start_time=start_time)

        try:
            self.query_one(CpuWidget).load_history(snapshots, time_span=seconds)
        except Exception:
            pass
        try:
            self.query_one(RamWidget).load_history(snapshots, time_span=seconds)
        except Exception:
            pass
        try:
            self.query_one(NetworkWidget).load_history(snapshots, time_span=seconds)
        except Exception:
            pass
        try:
            self.query_one(DiskWidget).load_history(snapshots, time_span=seconds)
        except Exception:
            pass

    def update_layout(self) -> None:
        """Delegates layout updates to WidgetManager."""
        if hasattr(self, "widget_manager"):
            self.widget_manager.update_layout()

    def update_display(self) -> None:
        """Fetch the latest snapshot and update widgets.

        Text labels always update every tick for a live feel.
        Graphs are only updated when at least one visual slot worth of time
        has passed — prevents meaningless scrolling on long history windows.
        """
        self.action_get_window_size()

        if not self.query_one("#main_container").display:
            return

        snapshot = self.db.get_latest()
        if snapshot is None:
            return

        now = time.time()
        # Approximate visual width in braille columns
        approx_graph_w = max(1, self.size.width * 2)
        slot_secs = self.history_duration / approx_graph_w
        # Graphs update at most once per visual slot, but at least as often as update_interval
        graph_refresh_due = (now - self._last_graph_refresh) >= max(slot_secs, self.update_interval)

        try:
            if graph_refresh_due:
                self.query_one(CpuWidget).update_cpu(snapshot)
            else:
                self.query_one(CpuWidget).update_text(snapshot)
        except Exception:
            pass
        try:
            if graph_refresh_due:
                self.query_one(RamWidget).update_ram(snapshot)
            else:
                self.query_one(RamWidget).update_text(snapshot)
        except Exception:
            pass
        try:
            if graph_refresh_due:
                self.query_one(NetworkWidget).update_network(snapshot)
            else:
                self.query_one(NetworkWidget).update_labels(snapshot)
        except Exception:
            pass
        try:
            if graph_refresh_due:
                self.query_one(DiskWidget).update_disk(snapshot)
            else:
                self.query_one(DiskWidget).update_labels(snapshot)
        except Exception:
            pass
        try:
            self.query_one(ProgrammListWidget).update_list()
        except Exception:
            pass

        if graph_refresh_due:
            self._last_graph_refresh = now

    def action_get_window_size(self) -> None:
        is_too_small = self.size.width < 80 or self.size.height < 24

        if is_too_small:
            self.query_one("#main_container").display = False
            self.query_one("#warning_container").display = True
        else:
            self.query_one("#main_container").display = True
            self.query_one("#warning_container").display = False

    def action_menu(self) -> None:
        menu = self.query_one(Menu)
        menu.display = not menu.display
        if menu.display:
            menu.populate_menu()
            try:
                from textual.widgets import SelectionList
                menu.query_one(SelectionList).focus()
            except Exception:
                pass

    def on_unmount(self) -> None:
        self.db.disconnect()


if __name__ == "__main__":
    app = MonitorifyApp()
    app.run()