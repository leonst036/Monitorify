from textual.app import App
from textual.widgets import Label
from textual.containers import Container

class MyApp(App):
    CSS = """
    #text { width: 100%; height: 100%; background: blue; }
    #overlay_wrapper { position: absolute; width: 100%; height: 100%; }
    #box { dock: right; width: 20; height: 5; background: red; }
    """
    def compose(self):
        yield Label("Content " * 100, id="text")
        with Container(id="overlay_wrapper"):
            yield Container(id="box")

    def on_mount(self):
        self.exit(self.query_one('#text').size.width)

if __name__ == "__main__":
    app = MyApp()
    print("Width:", app.run(headless=True, size=(100, 24)))
