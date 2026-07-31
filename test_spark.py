from textual.app import App, ComposeResult
from textual.widgets import Sparkline

class SparkApp(App):
    def compose(self) -> ComposeResult:
        yield Sparkline([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

if __name__ == "__main__":
    app = SparkApp()
    print(dir(Sparkline))
