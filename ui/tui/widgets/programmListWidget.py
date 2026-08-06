# pyrefly: ignore [missing-import]
from textual.containers import Container
# pyrefly: ignore [missing-import]
from textual.widgets import ListItem, ListView, Static
from stats.programmList import get_latest_process_items_data, start_process_cache_thread


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

    def compose(self):
        self.info_static = Static("Processes: 0", id="programm_list_info")
        yield self.info_static

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

    def update_list(self, force: bool = False):
        if not hasattr(self, "info_static") or not hasattr(self, "list_view"):
            return

        version, count, items_data = get_latest_process_items_data()
        if not force and version == self.last_cache_version:
            return

        self.last_cache_version = version
        self.info_static.update(f"Processes: {count}")

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
            existing_items[i].query_one(Static).update(sliced_data[i])

        if new_count > existing_count:
            new_items = [ListItem(Static(txt)) for txt in sliced_data[existing_count:]]
            self.list_view.extend(new_items)
        elif existing_count > new_count:
            for item in existing_items[new_count:]:
                item.remove()