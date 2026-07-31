from textual.widgets import Sparkline
from collections import deque

class HistorySparkline(Sparkline):
    """A Sparkline widget that maintains its own history of values."""
    
    def __init__(self, max_points: int = 50, **kwargs):
        """
        Args:
            max_points: The maximum number of data points to display in the graph.
        """
        # Pass any standard Sparkline arguments to the parent class (e.g., summary_function)
        super().__init__(**kwargs)
        self.data_history = deque([0] * max_points, maxlen=max_points)
        self.data = list(self.data_history)

    def update_value(self, new_value: float):
        """Appends a new value to the history and triggers a redraw."""
        self.data_history.append(new_value)
        self.data = list(self.data_history)
