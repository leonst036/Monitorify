from textual.containers import Container
from textual.widgets import Label

class StatusWidget(Container):
    BORDER_TITLE = "Status"
    
    def compose(self):
        self.uptime_label = Label(f"Uptime: {get_uptime()}")
        yield self.uptime_label
    
def get_uptime():
    with open("/proc/uptime", "r") as f:
        uptime = float(f.read().split()[0])
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
