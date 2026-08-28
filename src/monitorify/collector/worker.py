import time
from threading import Thread
from monitorify.stats import cpuStats, ramStats, networkStats, programmList, DiskStats
from monitorify.collector.schema import MetricSnapshot

from typing import Callable, Optional, Union

class Worker:
    def __init__(self, interval: Union[float, Callable[[], float]] = 1.0, on_data: Optional[Callable[[MetricSnapshot], None]] = None):
        self._interval = interval
        self._on_data = on_data
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = Thread(target=self._worker_loop)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def _get_interval(self) -> float:
        if callable(self._interval):
            try:
                return float(self._interval())
            except Exception:
                return 1.0
        try:
            return float(self._interval)
        except Exception:
            return 1.0

    def _worker_loop(self):
        while self._running:
            snapshot = self.collect()
            if self._on_data:
                try:
                    self._on_data(snapshot)
                except Exception as e:
                    print(f"Error handling metric snapshot: {e}")
            time.sleep(max(0.1, self._get_interval()))

    def collect(self) -> MetricSnapshot:
        return MetricSnapshot(
            timestamp=time.time(),
            cpu=cpuStats.get_cpu_usage(),
            ram=ramStats.get_ram_usage(),
            network=networkStats.get_network_usage(),
            processes_count=len(programmList.get_process_list()),
            disk_io=DiskStats.get_disk_IO(),
            disk_storage=DiskStats.get_disk_storage(),
        )