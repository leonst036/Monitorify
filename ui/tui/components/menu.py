from textual.containers import Container, Vertical
from textual.widgets import SelectionList, Static
from textual.widgets.selection_list import Selection


class Menu(Container):
    
    def compose(self):
        with Vertical(id="menu"):
            yield Static("[bold #61afef]M[/bold #61afef]enu", id="menu_title")
            yield SelectionList[str](id="widget_selector")

    def on_mount(self) -> None:
        self.populate_menu()

    def populate_menu(self) -> None:
        """Populates selection list with widget options and current states."""
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