import math
from textual.containers import Container


class WidgetManager:
    """Manages dynamic grid layouts for an arbitrary number of widgets."""

    def __init__(self, container: Container):
        self.container = container

    def update_layout(self) -> None:
        """Arranges visible widgets dynamically without layout gaps."""
        try:
            visible = [child for child in self.container.children if child.display]
            n = len(visible)
            if n == 0:
                return

            if n == 1:
                visible[0].styles.column_span = 2
                visible[0].styles.row_span = 2
            elif n == 2:
                for w in visible:
                    w.styles.column_span = 2
                    w.styles.row_span = 1
            else:
                cols = 2
                rows = math.ceil(n / cols)
                self.container.styles.grid_size_columns = cols
                self.container.styles.grid_size_rows = rows

                if n % 2 != 0:
                    visible[0].styles.column_span = 2
                    visible[0].styles.row_span = 1
                    for w in visible[1:]:
                        w.styles.column_span = 1
                        w.styles.row_span = 1
                else:
                    for w in visible:
                        w.styles.column_span = 1
                        w.styles.row_span = 1
        except Exception:
            pass
