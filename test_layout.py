import sys
from textual.app import App
from textual.widgets import Label
from textual.containers import Container
from ui.tui.widgets.statusWidget import StatusWidget

class TestApp(App):
    CSS_PATH = "ui/tui/css/tui.css"

    def compose(self):
        with Container(id="status_box_wrapper"):
            yield StatusWidget(id="status_box")
        yield Label("Graph placeholder", id="graph")

if __name__ == "__main__":
    app = TestApp()
    print("Parsed CSS")
