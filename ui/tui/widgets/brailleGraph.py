import time as _time
from textual.widget import Widget
from textual.app import RenderResult
from collections import deque
from rich.text import Text
from rich.style import Style

_SCALE_W = 7   # chars reserved for Y-axis scale
_DIM = Style(color="#3e4452")
_TICK = Style(color="#abb2bf")


def make_time_grid(snapshots, value_fn, time_span: float, width: int) -> list:
    """Map snapshots to a time-positioned list[float | None].
    Slots with no snapshot remain None — the graph draws nothing there.
    This ensures gaps where no daemon was running appear as empty space.
    """
    if not snapshots or time_span <= 0 or width <= 0:
        # Fall back to plain chronological list (no gap info)
        return [value_fn(s) for s in snapshots]

    now = _time.time()
    start = now - time_span
    grid: list = [None] * width

    for s in snapshots:
        if s.timestamp < start:
            continue
        pos = int((s.timestamp - start) / time_span * (width - 1))
        pos = max(0, min(width - 1, pos))
        grid[pos] = value_fn(s)

    return grid


class BrailleGraph(Widget):
    DEFAULT_CSS = """
    BrailleGraph {
        height: 1fr;
        min-height: 4;
    }
    """

    def __init__(
        self,
        data_lines: int = 1,
        max_points: int = 2000,
        color1: str = "#c678dd",
        color2: str = "#61afef",
        y_max: float | None = None,
        min_dots: int = 1,
        show_scale: bool = False,
        scale_fmt=None,
        show_timeline: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.data_lines = data_lines
        self.max_points = max_points
        self.color1 = Style(color=color1)
        self.color2 = Style(color=color2)
        self.y_max = y_max
        self.min_dots = min_dots
        self.show_scale = show_scale
        self.scale_fmt = scale_fmt or (lambda v: f"{v:.1f}%")
        self.show_timeline = show_timeline
        self.timeline_seconds: float = 0.0

        self.history1 = deque(maxlen=max_points)
        if self.data_lines > 1:
            self.history2 = deque(maxlen=max_points)

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _fmt_age(secs: float) -> str:
        """Format a number of seconds as a short age label."""
        if secs < 1:
            return "now"
        if secs < 60:
            return f"{int(secs)}s"
        if secs < 3600:
            return f"{int(secs / 60)}m"
        h = secs / 3600
        return f"{h:.0f}h" if h == int(h) else f"{h:.1f}h"

    def _build_timeline_row(self, width_chars: int) -> Text:
        """Build the timeline row shown below the graph."""
        row = list("─" * width_chars)

        if self.timeline_seconds > 0 and width_chars >= 8:
            num_ticks = min(5, max(2, width_chars // 8))
            for i in range(num_ticks):
                frac = i / (num_ticks - 1) if num_ticks > 1 else 0
                age = self.timeline_seconds * (1 - frac)
                label = self._fmt_age(age)
                pos = int(frac * (width_chars - 1))
                start = pos - len(label) // 2
                start = max(0, min(start, width_chars - len(label)))
                for j, ch in enumerate(label):
                    if 0 <= start + j < width_chars:
                        row[start + j] = ch

        text = Text()
        for ch in row:
            text.append(ch, _TICK if ch != "─" else _DIM)
        return text

    def _make_scale_label(self, value: float, style: Style) -> Text:
        """Right-aligned, separator-prefixed scale label."""
        label = self.scale_fmt(value)[-(_SCALE_W - 1):]
        text = Text()
        text.append("┤", _DIM)
        text.append(label.rjust(_SCALE_W - 1), style)
        return text

    # ── public API ────────────────────────────────────────────────────────────

    def load_history(
        self,
        values1: list,
        values2: list | None = None,
        timeline_seconds: float = 0.0,
    ) -> None:
        """Load historical data (list[float | None]) into the graph.
        None entries represent time slots with no data — nothing is drawn there.
        """
        self.timeline_seconds = timeline_seconds
        self.history1 = deque(values1, maxlen=self.max_points)
        if self.data_lines > 1 and values2 is not None:
            self.history2 = deque(values2, maxlen=self.max_points)
        self.refresh()

    def update_value(self, val1: float, val2: float = 0):
        self.history1.append(val1)
        if self.data_lines > 1:
            self.history2.append(val2)
        self.refresh()

    # ── render ────────────────────────────────────────────────────────────────

    def render(self) -> RenderResult:
        width_chars = self.size.width
        height_chars = self.size.height
        if width_chars <= 0 or height_chars <= 0:
            return ""

        timeline_rows = 1 if (self.show_timeline and height_chars > 2) else 0
        scale_w = _SCALE_W if self.show_scale else 0
        graph_chars = max(1, width_chars - scale_w)
        graph_rows = max(1, height_chars - timeline_rows)

        w = graph_chars * 2
        h = graph_rows * 4

        if w > self.max_points:
            self.max_points = w
            self.history1 = deque(self.history1, maxlen=self.max_points)
            if self.data_lines > 1:
                self.history2 = deque(self.history2, maxlen=self.max_points)

        grid = [[False] * w for _ in range(h)]
        data1 = list(self.history1)

        if self.data_lines == 1:
            real_vals = [v for v in data1 if v is not None]
            if self.y_max is not None:
                max_val = self.y_max
            else:
                max_val = max(real_vals) if real_vals else 1
                max_val = max(max_val, 1)

            num_points = min(w, len(data1))
            start_x = w - num_points

            for i in range(num_points):
                x = start_x + i
                val = data1[len(data1) - num_points + i]
                if val is None:
                    continue  # Gap — no daemon data for this slot
                dots = max(self.min_dots, round((val / max_val) * h))
                for y in range(h - dots, h):
                    if 0 <= y < h:
                        grid[y][x] = True

        else:
            data2 = list(self.history2)
            if self.y_max is not None:
                max_val = self.y_max
            else:
                real1 = [v for v in data1 if v is not None]
                real2 = [v for v in data2 if v is not None]
                max_val = max(
                    max(real1) if real1 else 1,
                    max(real2) if real2 else 1,
                    1,
                )

            center_y = h // 2
            num_points = min(w, len(data1))
            start_x = w - num_points

            for i in range(num_points):
                x = start_x + i
                idx = len(data1) - num_points + i
                v1 = data1[idx]
                v2 = data2[idx] if idx < len(data2) else None
                if v1 is None and v2 is None:
                    continue  # Gap — skip entirely
                v1 = v1 or 0.0
                v2 = v2 or 0.0
                dots1 = int((v1 / max_val) * (h / 2))
                if v1 > 0 and dots1 == 0:
                    dots1 = self.min_dots
                dots2 = int((v2 / max_val) * (h / 2))
                if v2 > 0 and dots2 == 0:
                    dots2 = self.min_dots
                for y in range(center_y - dots1, center_y):
                    if 0 <= y < h:
                        grid[y][x] = True
                for y in range(center_y, center_y + dots2):
                    if 0 <= y < h:
                        grid[y][x] = True

        braille_map = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]
        lines = []

        for row_idx, cy in enumerate(range(0, h, 4)):
            line_str = ""
            for cx in range(0, w, 2):
                char_val = 0x2800
                for dy in range(4):
                    for dx in range(2):
                        if grid[cy + dy][cx + dx]:
                            char_val += braille_map[dy][dx]
                line_str += chr(char_val)

            style = self.color1 if (self.data_lines == 1 or cy < h // 2) else self.color2
            line = Text(line_str, style=style)

            if self.show_scale:
                is_top = row_idx == 0
                is_bot = row_idx == graph_rows - 1
                is_mid = self.data_lines > 1 and row_idx == graph_rows // 2
                if is_top:
                    line.append_text(self._make_scale_label(max_val, self.color1))
                elif is_mid:
                    line.append_text(self._make_scale_label(0, Style(color="#5c6370")))
                elif is_bot:
                    bot_style = self.color2 if self.data_lines > 1 else self.color1
                    bot_val = max_val if self.data_lines > 1 else 0
                    line.append_text(self._make_scale_label(bot_val, bot_style))
                else:
                    line.append(" " * scale_w)

            lines.append(line)

        if timeline_rows:
            lines.append(self._build_timeline_row(width_chars))

        return Text("\n").join(lines)
