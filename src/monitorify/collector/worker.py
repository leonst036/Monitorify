import time
from threading import Thread
from monitorify.stats import cpuStats, ramStats, networkStats, programmList, DiskStats
from monitorify.collector.schema import MetricSnapshot

from typing import Callable, Optional

class Worker:
    def __init__(self, interval: float = 1.0, on_data: Optional[Callable[[MetricSnapshot], None]] = None):
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

    def _worker_loop(self):
        while self._running:
            snapshot = self.collect()
            if self._on_data:
                try:
                    self._on_data(snapshot)
                except Exception as e:
                    print(f"Error handling metric snapshot: {e}")
            time.sleep(self._interval)

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