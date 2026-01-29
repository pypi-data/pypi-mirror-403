import logging
import time
from typing import Any, Dict, Optional


class PerfTimer:
    def __init__(self, enabled: bool = False, logger: Optional[logging.Logger] = None):
        self.enabled = bool(enabled)
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = time.perf_counter()
        self._starts: Dict[str, float] = {}

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)

    def start(self, label: str) -> None:
        self._starts[label] = time.perf_counter()

    def time(self, label: str, use_global_start: bool = False) -> Optional[float]:
        if use_global_start:
            return (time.perf_counter() - self.start_time) * 1000
        start = self._starts.get(label)
        if start is None:
            return None
        return (time.perf_counter() - start) * 1000

    def log(
        self,
        label: str,
        use_global_start: bool = False,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Optional[float]:
        elapsed_ms = self.time(label, use_global_start=use_global_start)
        if elapsed_ms is None:
            return None
        if not self.enabled:
            return elapsed_ms
        if extra:
            self.logger.info("Timing: %s %.2f ms", label, elapsed_ms, extra=extra)
        else:
            self.logger.info("Timing: %s %.2f ms", label, elapsed_ms)
        return elapsed_ms
