from textual.widget import Widget
from textual.app import RenderResult
from collections import deque
from rich.text import Text
from rich.style import Style

class BrailleGraph(Widget):
    DEFAULT_CSS = """
    BrailleGraph {
        height: 1fr;
        min-height: 4;
    }
    """

    def __init__(self, data_lines: int = 1, max_points: int = 150, color1: str = "#c678dd", color2: str = "#61afef", y_max: float | None = None, min_dots: int = 1, **kwargs):
        super().__init__(**kwargs)
        self.data_lines = data_lines
        self.max_points = max_points
        self.color1 = Style(color=color1)
        self.color2 = Style(color=color2)
        self.y_max = y_max
        self.min_dots = min_dots
        
        self.history1 = deque(maxlen=max_points)
        if self.data_lines > 1:
            self.history2 = deque(maxlen=max_points)
        
    def update_value(self, val1: float, val2: float = 0):
        self.history1.append(val1)
        if self.data_lines > 1:
            self.history2.append(val2)
        self.refresh()
        
    def render(self) -> RenderResult:
        width_chars = self.size.width
        height_chars = self.size.height
        if width_chars <= 0 or height_chars <= 0: return ""

        w = width_chars * 2
        h = height_chars * 4
        grid = [[False]*w for _ in range(h)]
        
        data1 = list(self.history1)
        
        if self.data_lines == 1:
            if self.y_max is not None:
                max_val = self.y_max
            else:
                max_val = max(data1) if data1 else 1
                max_val = max(max_val, 1) # Prevent div by 0
            
            num_points = min(w, len(data1))
            start_x = w - num_points
            
            for i in range(num_points):
                x = start_x + i
                idx = len(data1) - num_points + i
                val = data1[idx]
                dots = max(self.min_dots, int((val / max_val) * h))
                
                # Draw up from bottom
                for y in range(h - dots, h):
                    if 0 <= y < h:
                        grid[y][x] = True
        else:
            data2 = list(self.history2)
            if self.y_max is not None:
                max_val = self.y_max
            else:
                max_val = max(max(data1) if data1 else 1, max(data2) if data2 else 1)
                max_val = max(max_val, 1)
            
            center_y = h // 2
            num_points = min(w, len(data1))
            start_x = w - num_points
            
            for i in range(num_points):
                x = start_x + i
                idx = len(data1) - num_points + i
                
                v1, v2 = data1[idx], data2[idx]
                dots1 = int((v1 / max_val) * (h / 2))
                dots2 = int((v2 / max_val) * (h / 2))
                
                # Draw up from center
                for y in range(center_y - dots1, center_y):
                    if 0 <= y < h: grid[y][x] = True
                
                # Draw down from center
                for y in range(center_y, center_y + dots2):
                    if 0 <= y < h: grid[y][x] = True

        braille_map = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]
        lines = []
        
        for cy in range(0, h, 4):
            line_str = ""
            for cx in range(0, w, 2):
                char_val = 0x2800
                for dy in range(4):
                    for dx in range(2):
                        if grid[cy+dy][cx+dx]:
                            char_val += braille_map[dy][dx]
                line_str += chr(char_val)
                
            if self.data_lines == 1:
                style = self.color1
            else:
                style = self.color1 if cy < (h // 2) else self.color2
                
            lines.append(Text(line_str, style=style))
            
        return Text("\n").join(lines)
