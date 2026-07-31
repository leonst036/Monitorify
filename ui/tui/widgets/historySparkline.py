# pyrefly: ignore [missing-import]
from textual.widgets import Sparkline
from collections import deque

class HistorySparkline(Sparkline):
    
    def __init__(self, max_points: int = 50, **kwargs):
        super().__init__(**kwargs)
        self.data_history = deque([0] * max_points, maxlen=max_points)
        self.data = list(self.data_history)

    def update_value(self, new_value: float):
        self.data_history.append(new_value)
        self.data = list(self.data_history)
