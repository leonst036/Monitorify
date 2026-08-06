# pyrefly: ignore [missing-import]
from textual.containers import Container
# pyrefly: ignore [missing-import]
from textual.widgets import ListItem, ListView, Static
from textual import on
from textual.events import Click
from stats.programmList import get_latest_process_items_data, start_process_cache_thread, _format_process_item


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


class ProgrammListWidget(Container):
    BORDER_TITLE = "PROC"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_cache_version = -1
        self.rendered_limit = 0
        self.sort_by = "cpu_ussage"
        self.sort_reverse = True

    def compose(self):
        self.info_static = Static("Processes: 0", id="programm_list_info")
        yield self.info_static

        header_str = f"[bold underline]{'PID':>6}[/bold underline]  [bold underline]{'NAME':<25}[/bold underline] [bold underline]{'RAM(MB)':>10}[/bold underline]  [bold underline]{'CPU(%)':>7}[/bold underline]"
        self.header_static = Static(header_str, id="programm_list_header")
        yield self.header_static

        self.list_view = FastListView(classes="programm_list_view")
        self.list_view.on_scroll_cb = self.check_expand
        yield self.list_view

    def on_mount(self):
        start_process_cache_thread(interval=1.5)
        self.update_list()

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
        if not force and version == self.last_cache_version:
            return

        self.last_cache_version = version
        self.info_static.update(f"Processes: {count}")
        
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
        existing_items = list(self.list_view.query(ListItem))
        new_count = len(sliced_data)
        existing_count = len(existing_items)

        # In-place update
        update_limit = min(existing_count, new_count)
        for i in range(update_limit):
            formatted_text = _format_process_item(sliced_data[i])
            existing_items[i].query_one(Static).update(formatted_text)

        if new_count > existing_count:
            new_items = [ListItem(Static(_format_process_item(d))) for d in sliced_data[existing_count:]]
            self.list_view.extend(new_items)
        elif existing_count > new_count:
            for item in existing_items[new_count:]:
                item.remove()