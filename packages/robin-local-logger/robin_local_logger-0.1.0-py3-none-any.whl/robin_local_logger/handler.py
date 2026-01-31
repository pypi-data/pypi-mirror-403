import logging
import os
import threading
from typing import Optional


class RobinFileHandler(logging.Handler):
    """Logging handler that writes to a file and trims oldest lines when file exceeds max size."""

    def __init__(self, filepath: str, max_mb: float = 5.0, encoding: Optional[str] = "utf-8"):
        super().__init__()
        self.filepath = filepath
        self.max_bytes = int(max_mb * 1024 * 1024)
        self.encoding = encoding or "utf-8"
        self.lock = threading.RLock()

        parent = os.path.dirname(self.filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record) + "\n"
            with self.lock:
                with open(self.filepath, "a", encoding=self.encoding) as f:
                    f.write(msg)
                self._enforce_size()
        except Exception:
            self.handleError(record)

    def _enforce_size(self) -> None:
        if self.max_bytes <= 0:
            return

        while os.path.exists(self.filepath) and os.path.getsize(self.filepath) > self.max_bytes:
            try:
                with open(self.filepath, "r", encoding=self.encoding) as f:
                    lines = f.readlines()
                if not lines:
                    break
                if len(lines) == 1:
                    open(self.filepath, "w", encoding=self.encoding).close()
                    break
                lines = lines[1:]
                with open(self.filepath, "w", encoding=self.encoding) as f:
                    f.writelines(lines)
            except Exception:
                break
