from textual.app import App
from textual.containers import Container, Horizontal, Vertical, Center
from textual.widgets import Static



class Menu(Container):
    def compose(self):
            with Vertical(id="menu"):
                yield Static("[bold #61afef]M[/bold #61afef]enü", id="menu_title")
                yield Static("Test 1")
                yield Static("Test 2")
                yield Static("Test 3")