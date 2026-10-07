from __future__ import annotations

import threading
from typing import Callable


class HeartbeatWorker:
    def __init__(self, interval_seconds: int, send_heartbeat: Callable[[str], object]) -> None:
        self.interval_seconds = interval_seconds
        self.send_heartbeat = send_heartbeat
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, status_provider: Callable[[], str]) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _loop() -> None:
            while not self._stop_event.is_set():
                try:
                    self.send_heartbeat(status_provider())
                except Exception:
                    pass
                self._stop_event.wait(self.interval_seconds)

        self._stop_event.clear()
        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
