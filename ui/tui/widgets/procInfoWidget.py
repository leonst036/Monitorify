# pyrefly: ignore [missing-import]
from textual.containers import Container
# pyrefly: ignore [missing-import]
from textual.widgets import Static
from stats.programmList import get_process_state, get_process_running_time


class ProcInfoWidget(Container):
    BORDER_TITLE = "Process"

    def compose(self):
        self.pid_label = Static("PID: -")
        yield self.pid_label

        self.name_label = Static("Name: -")
        yield self.name_label

        self.state_label = Static("State: -")
        yield self.state_label

        self.cpu_label = Static("CPU: -")
        yield self.cpu_label

        self.ram_label = Static("RAM: -")
        yield self.ram_label

        self.uptime_label = Static("Uptime: -")
        yield self.uptime_label

    def update_process(self, d: dict):
        pid = d.get("pid", 0)
        name = d.get("name", "Unknown")
        state = d.get("state") or (get_process_state(pid) if pid else "Unknown")
        uptime = d.get("running_time") or (get_process_running_time(pid) if pid else "Unknown")
        cpu = d.get("cpu_ussage", 0.0)
        ram = d.get("ram_ussage", 0.0)

        self.border_title = f"PID: {pid}"
        self.pid_label.update(f"PID: {pid}")
        self.name_label.update(f"Name: {name}")
        self.state_label.update(f"State: {state}")
        self.cpu_label.update(f"CPU: {cpu:.1f}%")
        self.ram_label.update(f"RAM: {ram:.1f} MB")
        self.uptime_label.update(f"Uptime: {uptime}")
