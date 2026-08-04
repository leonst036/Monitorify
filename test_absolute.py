from textual.app import App
from textual.widgets import Label
from textual.containers import Container

class MyApp(App):
    CSS = """
    #base { width: 100%; height: 100%; layers: base overlay; }
    #graph { width: 100%; height: 100%; background: blue; layer: base; }
    #wrapper { position: absolute; width: 100%; height: 100%; align: right top; layer: overlay; }
    #box { width: 20; height: 5; background: red; }
    """
    def compose(self):
        with Container(id="base"):
            yield Label("Graph " * 50, id="graph")
            with Container(id="wrapper"):
                yield Container(id="box")

    def on_mount(self):
        self.exit(self.query_one('#graph').size.width)

if __name__ == "__main__":
    app = MyApp()
    print("Graph width:", app.run(headless=True, size=(100, 24)))
