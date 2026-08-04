from textual.containers import Container
from textual.widgets import Static
import socket

class StatusWidget(Container):
    BORDER_TITLE = "Status"
    
    def compose(self):
        self.system_info = Static(f"System: {get_kernel_version()}")
        yield self.system_info

        self.hostname = Static(f"Hostname: {get_hostname()}")
        yield self.hostname
        
        self.uptime = Static(f"Uptime: {get_uptime()}")
        yield self.uptime

    def on_mount(self):
        self.set_interval(1, self.update_uptime)

    def update_uptime(self):
        self.uptime.update(f"Uptime: {get_uptime()}")
    
def get_uptime():
    with open("/proc/uptime", "r") as f:
        uptime = float(f.read().split()[0])
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_hostname():
    return socket.gethostname()

def get_OS_name():
    with open("/etc/os-release", "r") as f:
        for line in f:
            if line.startswith("NAME="):
                name = line.split("=")[1].strip().strip('"')
                return name.replace("Linux", "").strip()
    return "Unknown"

def get_kernel_version():
    with open("/proc/version", "r") as f:
        return f.read().split()[2]