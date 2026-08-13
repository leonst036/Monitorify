# pyrefly: ignore [missing-import]
from textual.containers import Container, Vertical
# pyrefly: ignore [missing-import]
from textual.widgets import SelectionList, Static, Select, Input
# pyrefly: ignore [missing-import]
from textual.widgets.selection_list import Selection

INTERVAL_OPTIONS: list[tuple[str, float]] = [
    ("0.25s", 0.25),
    ("0.50s", 0.5),
    ("1.00s", 1.0),
    ("2.00s", 2.0),
    ("5.00s", 5.0),
]

HISTORY_OPTIONS: list[tuple[str, float | None]] = [
    ("1m", 60.0),
    ("5m", 300.0),
    ("10m", 600.0),
    ("30m", 1800.0),
    ("1h", 3600.0),
    ("custom", None)
]


class Menu(Container):
    
    def compose(self):
        with Vertical(id="menu"):
            yield Static("[bold #61afef]M[/bold #61afef]enu", id="menu_title")
            yield Static("[bold #abb2bf]Widgets:[/bold #abb2bf]", classes="menu_label")
            yield SelectionList[str](id="widget_selector")
            yield Static("[bold #abb2bf]Update Interval:[/bold #abb2bf]", classes="menu_label")
            yield Select(
                options=INTERVAL_OPTIONS,
                value=1.0,
                id="interval_select",
                allow_blank=False,
            )
            yield Static("[bold #abb2bf]History Duration:[/bold #abb2bf]", classes="menu_label")
            yield Select(
                options=HISTORY_OPTIONS,
                value=60.0,
                id="history_select",
                allow_blank=False,
            )
            # Render custom history input
            yield Input(
                placeholder="Duration e.g. 120s, 2h, 1d, 1wm",
                id="custom_history_input",
            )

    def on_mount(self) -> None:
        # Hide custom input initially
        custom_input = self.query_one("#custom_history_input", Input)
        custom_input.display = False

        self.populate_menu()

    def populate_menu(self) -> None:
        """Populates selection list with widget options and updates interval select value."""
        try:
            selection_list = self.query_one(SelectionList)
            selection_list.clear_options()
            for name, widget_id in self.get_available_widgets().items():
                widget = self.app.query_one(f"#{widget_id}")
                selection_list.add_option(
                    Selection(prompt=name, value=name, initial_state=widget.display)
                )
        except Exception:
            pass

        try:
            interval_select = self.query_one("#interval_select", Select)
            current_interval = getattr(self.app, "update_interval", 1.0)
            if interval_select.value != current_interval:
                interval_select.value = current_interval
        except Exception:
            pass

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handles changes in the update interval and history duration selectors."""
        if event.select.id == "interval_select" and event.value is not Select.BLANK:
            if hasattr(self.app, "set_update_interval"):
                self.app.set_update_interval(float(event.value))

        elif event.select.id == "history_select":
            custom_input = self.query_one("#custom_history_input", Input)
            is_custom = event.value is None
            
            custom_input.display = is_custom
            if is_custom:
                custom_input.focus()

    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Toggles widget visibility based on selection changes."""
        selected_names = event.selection_list.selected
        for name, widget_id in self.get_available_widgets().items():
            try:
                widget = self.app.query_one(f"#{widget_id}")
                widget.display = name in selected_names
            except Exception:
                pass
        if hasattr(self.app, "update_layout"):
            self.app.update_layout()

    def get_available_widgets(self) -> dict[str, str]:
        """Returns a map of {widget_name: widget_id} from main_container."""
        widgets_map = {}
        try:
            main_container = self.app.query_one("#main_container")
            for child in main_container.children:
                raw_title = getattr(child, "BORDER_TITLE", child.__class__.__name__)
                clean_name = raw_title.split()[0] if raw_title else child.__class__.__name__
                widget_id = child.id or child.__class__.__name__.lower()
                widgets_map[clean_name] = widget_id
        except Exception:
            pass
        return widgets_map

    def select_widget(self, widget_name: str) -> str | None:
        """Returns the widget ID for a given widget name."""
        widgets_map = self.get_available_widgets()
        for name, widget_id in widgets_map.items():
            if name.upper() == widget_name.upper():
                return widget_id
        return None

    def toggle_widget(self, widget: str) -> None:
        """Toggles widget visibility by widget name."""
        widget_id = self.select_widget(widget)
        if widget_id:
            if not widget_id.startswith("#"):
                widget_id = f"#{widget_id}"

            try:
                widget_to_toggle = self.app.query_one(widget_id)
                widget_to_toggle.display = not widget_to_toggle.display
                if hasattr(self.app, "update_layout"):
                    self.app.update_layout()
            except Exception:
                pass