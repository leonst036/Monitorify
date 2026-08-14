from typing import List, Optional, Any, Callable
from monitorify.collector.worker import Worker


class Manager:
    def __init__(self, db: Optional[Any] = None, interval: float = 1.0):
        self._workers: List[Worker] = []
        self._interval = interval
        if db is None:
            from monitorify.storage.db import Database
            self._db = Database()
        else:
            self._db = db
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def add_worker(self, worker: Worker):
        self._workers.append(worker)

    def setup_default_worker(self) -> Worker:
        """Create and register default metric worker connected to Database."""
        worker = Worker(interval=self._interval, on_data=self._db.save)
        self.add_worker(worker)
        return worker

    def start(self):
        if self._is_running:
            return
        self._db.connect()
        self._is_running = True
        if not self._workers:
            self.setup_default_worker()
        for worker in self._workers:
            worker.start()

    def stop(self):
        if not self._is_running:
            return
        for worker in self._workers:
            worker.stop()
        self._db.disconnect()
        self._is_running = False


    