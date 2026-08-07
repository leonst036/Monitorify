from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple

@dataclass
class NetworkMetrics:
    rx_bytes: float
    tx_bytes: float

@dataclass
class MetricSnapshot:
    timestamp: float
    cpu: float
    ram: float
    network: Tuple[float, float]
    processes_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass object into a standard dictionary."""
        return asdict(self)
