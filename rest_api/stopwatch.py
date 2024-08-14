import time


class Stopwatch:
    def __init__(self):
        self._start_time = None
        self._elapsed_time = 0.0
        self._running = False

    def start(self):
        if not self._running:
            self._start_time = time.time()
            self._running = True

    def stop(self):
        if self._running:
            self._elapsed_time += time.time() - self._start_time
            self._running = False

    def restart(self):
        self._start_time = time.time()
        self._elapsed_time = 0.0
        self._running = True

    def reset(self):
        self._start_time = None
        self._elapsed_time = 0.0
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def total_millis(self) -> int:
        return int(self.total_seconds * 1000)

    @property
    def total_seconds(self) -> float:
        if self._running:
            return self._elapsed_time + (time.time() - self._start_time)
        return self._elapsed_time

    @property
    def total_minutes(self) -> float:
        return self.total_seconds / 60

    @property
    def total_hours(self) -> float:
        return self.total_minutes / 60
