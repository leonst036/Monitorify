import time
from threading import Thread
from stats import cpuStats, ramStats, networkStats, programmList
from collector.schema import MetricSnapshot

class Worker:
    def __init__(self, interval: float = 1.0):
        self._interval = interval
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
            self.collect()
            time.sleep(self._interval)

    def collect(self) -> MetricSnapshot:
        return MetricSnapshot(
            timestamp=time.time(),
            cpu=cpuStats.get_cpu_usage(),
            ram=ramStats.get_ram_usage(),
            network=networkStats.get_network_usage(),
            processes_count=len(programmList.get_process_list())
        )