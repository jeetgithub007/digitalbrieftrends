"""
Trend Pipeline Cache — thread-safe in-memory store with timestamp tracking.
"""
import time
import threading

class TrendCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = None
        self._updated_at = None
        self._refresh_count = 0
        self._errors = []

    def update(self, data):
        with self._lock:
            self._data = data
            self._updated_at = time.time()
            self._refresh_count += 1

    def get(self):
        with self._lock:
            return self._data, self._updated_at, self._refresh_count

    def add_error(self, error_msg):
        with self._lock:
            self._errors.append({
                "time": time.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
                "error": error_msg,
            })
            if len(self._errors) > 20:
                self._errors = self._errors[-20:]

    def status(self):
        with self._lock:
            age_sec = time.time() - self._updated_at if self._updated_at else None
            return {
                "data_available": self._data is not None,
                "last_updated": time.strftime(
                    "%Y-%m-%dT%H:%M:%S+05:30",
                    time.localtime(self._updated_at)
                ) if self._updated_at else None,
                "age_seconds": round(age_sec, 1) if age_sec else None,
                "refresh_count": self._refresh_count,
                "total_trends": len(self._data) if self._data else 0,
                "recent_errors": self._errors[-5:] if self._errors else [],
            }

# Global singleton
cache = TrendCache()
