import time
import sys
from pathlib import Path

# pyrefly: ignore [missing-import]
from textual.app import App, ComposeResult
# pyrefly: ignore [missing-import]
from textual.widgets import Header, Footer, Label
from textual.containers import Container, Center, Middle
from textual.events import Click
from monitorify.ui.tui.widgets.cpuWidget import CpuWidget
from monitorify.ui.tui.widgets.ramWidget import RamWidget
from monitorify.ui.tui.widgets.networkWidget import NetworkWidget
from monitorify.ui.tui.widgets.diskWidget import DiskWidget
from monitorify.ui.tui.components.menu import Menu
from monitorify.ui.tui.components.widgetManager import WidgetManager
from monitorify.ui.tui.widgets.programmListWidget import ProgrammListWidget
from monitorify.storage import Database
from monitorify import config
from monitorify.config.configManager import configManager


class MonitorifyApp(App):
    CSS_PATH = "css/tui.css"

    TITLE = "Monitorify"
    AUTO_FOCUS = None
    BINDINGS = [
        ("q", "quit"),
        ("c", "quit"),
        ("m", "menu"),
        ("slash", "search_process"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = configManager(str(config.CONFIG_PATH))
        # Read-only DB connection
        self.db = Database(config.DB_PATH)
        self.db.connect()
        # Load saved preferences from config
        self.update_interval = float(self.config_manager.get("update_interval", 1.0))
        self.history_duration: float = float(self.config_manager.get("history_duration", 60.0))
        self._last_graph_refresh: float = 0.0

    def persist_config(self) -> None:
        visible_widgets = []
        for widget_id in ["cpu_widget", "ram_widget", "programmList_widget", "network_widget", "disk_widget"]:
            try:
                if self.query_one(f"#{widget_id}").display:
                    visible_widgets.append(widget_id)
            except Exception:
                pass

        self.config_manager.save_config({
            "update_interval": float(self.update_interval),
            "history_duration": float(self.history_duration),
            "visible_widgets": visible_widgets,
        })

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
        saved_visible = self.config_manager.get("visible_widgets")
        if saved_visible is not None:
            visible_widgets = set(saved_visible)
        else:
            visible_widgets = set()
        for widget_id in ["cpu_widget", "ram_widget", "programmList_widget", "network_widget", "disk_widget"]:
            try:
                widget = self.query_one(f"#{widget_id}")
                widget.display = widget_id in visible_widgets if saved_visible is not None else widget.display
            except Exception:
                pass
        self.update_layout()
        # Ensure search input does not steal focus on startup
        self.set_focus(None)
        # Load history from DB on startup
        self.call_after_refresh(self._load_initial_history)
        self.update_timer = self.set_interval(self.update_interval, self.update_display)

    def _load_initial_history(self) -> None:
        """Load history from DB after the first render so widgets have their sizes."""
        self.set_history_duration(self.history_duration, persist=False)

    def set_update_interval(self, seconds: float) -> None:
        """Updates the graph refresh interval."""
        self.update_interval = seconds
        if hasattr(self, "update_timer") and self.update_timer:
            self.update_timer.stop()
        self.update_timer = self.set_interval(self.update_interval, self.update_display)
        self.persist_config()

    def set_history_duration(self, seconds: float, persist: bool = True) -> None:
        """Load historical metrics from DB and push them into all graph widgets."""
        self.history_duration = seconds
        if persist:
            self.persist_config()
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
        if getattr(self, "_is_suspended", False):
            return

        self.action_get_window_size()

        if not self.query_one("#main_container").display:
            return


        snapshot = self.db.get_latest()
        if snapshot is None:
            return

        now = time.time()
        approx_graph_w = max(1, self.size.width * 2)
        slot_secs = self.history_duration / approx_graph_w
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

    def action_search_process(self) -> None:
        try:
            programm_widget = self.query_one(ProgrammListWidget)
            if programm_widget.display:
                from textual.widgets import Input
                search_input = programm_widget.query_one("#proc_search_input", Input)
                search_input.focus()
        except Exception:
            pass

    def on_click(self, event: Click) -> None:
        try:
            programm_widget = self.query_one(ProgrammListWidget)
            programm_widget.handle_global_click(event)
        except Exception:
            pass

    def connect_to_remote(self, host_id: int) -> None:
        """Connects to a remote host by ID after suspending the TUI."""
        host = self.db.get_host(host_id)
        if not host:
            return

        self._is_suspended = True
        session_started = False
        try:
            with self.suspend():
                try:
                    from monitorify.remote.connector import connect_and_run

                    session_started = connect_and_run(
                        host=host["ip"],
                        port=host.get("port") or 22,
                        username=host.get("username"),
                        password=host.get("password"),
                        key_filename=host.get("key_filename"),
                        pause_on_exit=True,
                    )
                except Exception as e:
                    print(f"Error launching remote session: {e}")
                    input("Press Enter to return...")
        except Exception:
            pass
        finally:
            self._is_suspended = False

        if session_started:
            self.exit()
            return

        try:
            menu = self.query_one(Menu)
            menu.display = False
        except Exception:
            pass
        self.refresh(layout=True)

    def prompt_add_remote(self) -> None:
        """Suspends the TUI and runs interactive remote host setup."""
        self._is_suspended = True
        try:
            with self.suspend():
                from monitorify.remote.addRemote import add_remote

                print("\n=== Add Remote Host ===")
                try:
                    add_remote(db=self.db)
                except KeyboardInterrupt:
                    print("\nCancelled.")
                except Exception as e:
                    print(f"\nError: {e}")
                input("\nPress Enter to return...")
        except Exception:
            pass
        finally:
            self._is_suspended = False
            try:
                menu = self.query_one(Menu)
                menu.populate_menu()
            except Exception:
                pass
            self.refresh(layout=True)

    def on_unmount(self) -> None:
        self.db.disconnect()



if __name__ == "__main__":
    app = MonitorifyApp()
    app.run()