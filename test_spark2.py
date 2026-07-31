from textual.app import App, ComposeResult
from textual.widgets import Sparkline

class SparkApp(App):
    def compose(self) -> ComposeResult:
        # Give it a known max_value if possible
        yield Sparkline([10, 20, 30, 40, 50, 60, 70, 80, 90, 100], summary_function=max)

if __name__ == "__main__":
    app = SparkApp()
    import inspect
    print(inspect.signature(Sparkline.__init__))
