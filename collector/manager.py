class Manager:
    def __init__(self, interval: float = 1.0):
        self._workers = []
        self._interval = interval

    def add_worker(self, worker):
        self._workers.append(worker)

    def start(self):
        for worker in self._workers:
            worker.start()

    def stop(self):
        for worker in self._workers:
            worker.stop()

    