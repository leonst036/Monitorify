# pyrefly: ignore [missing-import]
from textual.containers import Container, Horizontal
# pyrefly: ignore [missing-import]
from textual.widgets import ListItem, ListView, Static, Input
from textual import on, events
from textual.events import Click
from monitorify.stats.programmList import (
    get_latest_process_items_data,
    start_process_cache_thread,
    _format_process_item,
)
from monitorify.ui.tui.widgets.procInfoWidget import ProcInfoWidget


class FastListView(ListView):
    """ListView subclass with instant reactive callbacks on scroll or index changes."""

    def watch_scroll_y(self, old_value: float, new_value: float) -> None:
        super().watch_scroll_y(old_value, new_value)
        if hasattr(self, "on_scroll_cb") and self.on_scroll_cb:
            self.on_scroll_cb()

    def watch_index(self, old_value: int | None, new_value: int | None) -> None:
        super().watch_index(old_value, new_value)
        if hasattr(self, "on_scroll_cb") and self.on_scroll_cb:
            self.on_scroll_cb()
        if hasattr(self, "on_highlight_cb") and self.on_highlight_cb:
            self.on_highlight_cb()


class ProgrammListWidget(Container):
    BORDER_TITLE = "PROC"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_cache_version = -1
        self.rendered_limit = 0
        self.sort_by = "cpu_ussage"
        self.sort_reverse = True
        self.current_sorted_data = []
        self.total_count = 0
        self.active_info_pid = None
        self.search_query = ""
        self.filtered_count = 0

    def compose(self):
        with Horizontal(id="programm_list_top"):
            self.info_static = Static("Processes: 0", id="programm_list_info")
            yield self.info_static
            self.search_input = Input(placeholder="Search (/) ...", id="proc_search_input")
            yield self.search_input

        header_str = f"[bold underline]{'PID':>6}[/bold underline]  [bold underline]{'NAME':<25}[/bold underline] [bold underline]{'RAM(MB)':>10}[/bold underline]  [bold underline]{'CPU(%)':>7}[/bold underline]"
        self.header_static = Static(header_str, id="programm_list_header")
        yield self.header_static

        self.list_view = FastListView(classes="programm_list_view")
        self.list_view.on_scroll_cb = self.check_expand
        self.list_view.on_highlight_cb = self.update_details
        yield self.list_view

    def on_mount(self):
        start_process_cache_thread(interval=1.5)
        self.proc_info_box = ProcInfoWidget(id="proc_info_box")
        self.screen.mount(self.proc_info_box)
        self.update_list()

    def update_info_box_position(self):
        if hasattr(self, "proc_info_box") and self.proc_info_box:
            box_width = 30  # matches StatusWidget width
            self.proc_info_box.styles.offset = (
                self.region.x + self.size.width - box_width,
                self.region.y,
            )

    def on_resize(self):
        self.update_info_box_position()

    @on(ListView.Selected)
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.index if getattr(event, "index", None) is not None else self.list_view.index
        if idx is not None and 0 <= idx < len(self.current_sorted_data):
            d = self.current_sorted_data[idx]
            pid = d.get("pid")
            if pid is not None:
                self.active_info_pid = pid
                self.update_details()

    @on(ListView.Highlighted)
    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if self.active_info_pid is not None:
            idx = getattr(event, "item_index", None)
            if idx is None:
                idx = self.list_view.index
            if idx is not None and 0 <= idx < len(self.current_sorted_data):
                d = self.current_sorted_data[idx]
                pid = d.get("pid")
                if pid is not None:
                    self.active_info_pid = pid
                    self.update_details()

    @on(Input.Changed, "#proc_search_input")
    def on_search_changed(self, event: Input.Changed) -> None:
        self.search_query = event.value
        self.rendered_limit = 0
        if hasattr(self, "list_view"):
            self.list_view.scroll_to(y=0)
        self.update_list(force=True)

    @on(Input.Submitted, "#proc_search_input")
    def on_search_submitted(self, event: Input.Submitted) -> None:
        if hasattr(self, "list_view"):
            self.list_view.focus()
            if self.list_view.index is None and len(self.list_view.children) > 0:
                self.list_view.index = 0

    def on_key(self, event: events.Key) -> None:
        if not hasattr(self, "search_input") or not hasattr(self, "list_view"):
            return
        if self.search_input.has_focus:
            if event.key == "escape":
                if self.search_input.value:
                    self.search_input.value = ""
                self.list_view.focus()
                event.prevent_default()
                event.stop()
            elif event.key == "down":
                self.list_view.focus()
                if self.list_view.index is None and len(self.list_view.children) > 0:
                    self.list_view.index = 0
                event.prevent_default()
                event.stop()
        elif self.list_view.has_focus:
            if event.key == "slash":
                self.search_input.focus()
                event.prevent_default()
                event.stop()

    def is_child_of_proc_info_box(self, widget) -> bool:
        curr = widget
        while curr:
            if curr is getattr(self, "proc_info_box", None) or getattr(curr, "id", None) == "proc_info_box":
                return True
            curr = getattr(curr, "parent", None)
        return False

    def is_search_input(self, widget) -> bool:
        curr = widget
        while curr:
            if getattr(curr, "id", None) == "proc_search_input":
                return True
            curr = getattr(curr, "parent", None)
        return False

    def get_clicked_list_item_index(self, widget) -> int | None:
        if not hasattr(self, "list_view"):
            return None
        curr = widget
        while curr:
            if isinstance(curr, ListItem) and curr.parent is self.list_view:
                try:
                    items = list(self.list_view.query(ListItem))
                    return items.index(curr)
                except ValueError:
                    return None
            curr = getattr(curr, "parent", None)
        return None

    def is_header(self, widget) -> bool:
        curr = widget
        while curr:
            if getattr(curr, "id", None) == "programm_list_header":
                return True
            curr = getattr(curr, "parent", None)
        return False

    def handle_global_click(self, event: Click) -> None:
        item_idx = self.get_clicked_list_item_index(event.widget)
        if item_idx is not None:
            if 0 <= item_idx < len(self.current_sorted_data):
                self.active_info_pid = self.current_sorted_data[item_idx].get("pid")
                self.update_details()
            return

        if self.is_child_of_proc_info_box(event.widget) or self.is_header(event.widget) or self.is_search_input(event.widget):
            return

        if self.active_info_pid is not None:
            self.active_info_pid = None
            self.update_details()

    def update_selection_classes(self) -> None:
        """Update selected class on ListItems based on active_info_pid."""
        if not hasattr(self, "list_view"):
            return
        items = list(self.list_view.query(ListItem))
        for i, item in enumerate(items):
            is_selected = (
                self.active_info_pid is not None
                and i < len(self.current_sorted_data)
                and self.current_sorted_data[i].get("pid") == self.active_info_pid
            )
            item.set_class(is_selected, "selected")

    def update_details(self) -> None:
        if not hasattr(self, "info_static") or not hasattr(self, "list_view"):
            return

        self.update_selection_classes()
        if self.search_query.strip():
            self.info_static.update(f"Processes: {getattr(self, 'filtered_count', len(self.current_sorted_data))}/{self.total_count}")
        else:
            self.info_static.update(f"Processes: {self.total_count}")

        if not self.display or self.active_info_pid is None:
            if hasattr(self, "proc_info_box") and self.proc_info_box:
                self.proc_info_box.display = False
            return

        self.update_info_box_position()

        active_data = None
        for d in self.current_sorted_data:
            if d.get("pid") == self.active_info_pid:
                active_data = d
                break

        if active_data and hasattr(self, "proc_info_box") and self.proc_info_box:
            self.proc_info_box.update_process(active_data)
            self.proc_info_box.display = True
        else:
            if hasattr(self, "proc_info_box") and self.proc_info_box:
                self.proc_info_box.display = False

    def check_expand(self):
        if not hasattr(self, "list_view"):
            return
        idx = self.list_view.index or 0
        scroll_y = int(self.list_view.scroll_y)
        height = self.size.height or 20
        needed = max(idx, scroll_y + height) + 30
        if needed > self.rendered_limit:
            self.rendered_limit = max(self.rendered_limit, needed + int(height * 4))
            self.update_list(force=True)

    @on(Click, "#programm_list_header")
    def on_header_click(self, event: Click) -> None:
        x = event.x
        new_sort = self.sort_by
        if x <= 7:
            new_sort = "pid"
        elif x <= 34:
            new_sort = "name"
        elif x <= 46:
            new_sort = "ram_ussage"
        else:
            new_sort = "cpu_ussage"
            
        if self.sort_by == new_sort:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_by = new_sort
            self.sort_reverse = True if new_sort in ["ram_ussage", "cpu_ussage"] else False
            
        self.update_list(force=True)

    def update_list(self, force: bool = False):
        if not hasattr(self, "info_static") or not hasattr(self, "list_view"):
            return

        version, count, items_data = get_latest_process_items_data()
        self.total_count = count

        if not force and version == self.last_cache_version:
            self.update_details()
            return

        self.last_cache_version = version

        # Filter by search query if present
        query = self.search_query.strip().lower()
        if query:
            items_data = [
                d for d in items_data
                if query in str(d.get("name", "")).lower() or query in str(d.get("pid", ""))
            ]

        self.filtered_count = len(items_data)

        # Sort items_data based on user selection
        if self.sort_by in ["pid", "ram_ussage", "cpu_ussage"]:
            items_data.sort(key=lambda d: d.get(self.sort_by, 0), reverse=self.sort_reverse)
        else:
            items_data.sort(key=lambda d: str(d.get(self.sort_by, "")).lower(), reverse=self.sort_reverse)

        height = self.size.height or 20
        max_visible = max(20, int(height * 2.5))
        current_index = self.list_view.index or 0
        scroll_y = int(self.list_view.scroll_y)

        needed = max(current_index, scroll_y + height) + 30
        self.rendered_limit = max(self.rendered_limit, max_visible, needed)

        sliced_data = items_data[:self.rendered_limit]
        self.current_sorted_data = sliced_data
        existing_items = list(self.list_view.query(ListItem))
        new_count = len(sliced_data)
        existing_count = len(existing_items)

        # In-place update
        update_limit = min(existing_count, new_count)
        for i in range(update_limit):
            formatted_text = _format_process_item(sliced_data[i])
            existing_items[i].query_one(Static).update(formatted_text)
            is_selected = (
                self.active_info_pid is not None
                and sliced_data[i].get("pid") == self.active_info_pid
            )
            existing_items[i].set_class(is_selected, "selected")

        if new_count > existing_count:
            new_items = []
            for d in sliced_data[existing_count:]:
                item = ListItem(Static(_format_process_item(d)))
                if self.active_info_pid is not None and d.get("pid") == self.active_info_pid:
                    item.add_class("selected")
                new_items.append(item)
            self.list_view.extend(new_items)
        elif existing_count > new_count:
            for item in existing_items[new_count:]:
                item.remove()

        self.update_details()