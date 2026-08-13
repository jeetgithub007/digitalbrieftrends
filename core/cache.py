"""Thread-safe in-memory cache for trend data."""
import time
import threading


class TrendCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = None
        self._updated_at = None
        self._count = 0
        self._errors = []
        self._saved = set()
        self._dismissed = set()

    def update(self, data):
        with self._lock:
            self._data = data
            self._updated_at = time.time()
            self._count += 1

    def get(self):
        with self._lock:
            return self._data, self._updated_at, self._count

    def add_error(self, msg):
        with self._lock:
            self._errors.append({
                "time": time.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
                "error": str(msg)[:200],
            })
            if len(self._errors) > 20:
                self._errors = self._errors[-20:]

    def status(self):
        with self._lock:
            age = time.time() - self._updated_at if self._updated_at else None
            return {
                "data_available": self._data is not None,
                "last_updated": time.strftime(
                    "%Y-%m-%dT%H:%M:%S+05:30",
                    time.localtime(self._updated_at)
                ) if self._updated_at else None,
                "age_seconds": round(age, 1) if age else None,
                "refresh_count": self._count,
                "total_trends": len(self._data) if self._data else 0,
                "recent_errors": self._errors[-5:] if self._errors else [],
                "saved_count": len(self._saved),
                "dismissed_count": len(self._dismissed),
            }

    # ── Save / Dismiss (additive state) ──
    def save(self, title):
        with self._lock:
            self._saved.add(title)
            self._dismissed.discard(title)
        return {"saved": True, "title": title}

    def dismiss(self, title):
        with self._lock:
            self._dismissed.add(title)
            self._saved.discard(title)
        return {"dismissed": True, "title": title}

    def saved_titles(self):
        with self._lock:
            return sorted(self._saved)

    def dismissed_titles(self):
        with self._lock:
            return sorted(self._dismissed)


# Global singleton
cache = TrendCache()
