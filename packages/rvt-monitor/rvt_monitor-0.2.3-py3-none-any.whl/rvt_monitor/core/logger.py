"""Logging system with file output and WebSocket broadcast."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import platformdirs

# App data directory
APP_NAME = "RVT-Monitor"
DATA_DIR = Path(platformdirs.user_data_dir(APP_NAME))
LOG_DIR = DATA_DIR / "logs"


def ensure_log_dir():
    """Ensure log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_log_file_path(date: Optional[datetime] = None) -> Path:
    """Get log file path for a specific date."""
    if date is None:
        date = datetime.now()
    return LOG_DIR / f"{date.strftime('%Y-%m-%d')}.log"


class WebSocketHandler(logging.Handler):
    """Logging handler that broadcasts to WebSocket clients."""

    def __init__(self):
        super().__init__()
        self.broadcast_callback: Optional[Callable] = None

    def emit(self, record: logging.LogRecord):
        if self.broadcast_callback:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(
                        self.broadcast_callback(record.levelname, self.format(record))
                    )
            except Exception:
                pass


class AppLogger:
    """Application logger with file and WebSocket output."""

    def __init__(self):
        self.logger = logging.getLogger("rvt_monitor")
        self.logger.setLevel(logging.DEBUG)
        self.ws_handler: Optional[WebSocketHandler] = None
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup logging handlers."""
        ensure_log_dir()

        # File handler (daily rotation)
        file_path = get_log_file_path()
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        self.logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            "[%(levelname)s] %(message)s"
        ))
        self.logger.addHandler(console_handler)

        # WebSocket handler
        self.ws_handler = WebSocketHandler()
        self.ws_handler.setLevel(logging.INFO)
        self.ws_handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(self.ws_handler)

    def set_ws_callback(self, callback: Callable):
        """Set WebSocket broadcast callback."""
        if self.ws_handler:
            self.ws_handler.broadcast_callback = callback

    def debug(self, msg: str):
        self.logger.debug(msg)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)


# Global logger instance
logger = AppLogger()


def get_log_files() -> list[dict]:
    """Get list of log files."""
    ensure_log_dir()
    files = []
    for f in sorted(LOG_DIR.glob("*.log"), reverse=True):
        stat = f.stat()
        files.append({
            "name": f.name,
            "date": f.stem,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return files


def read_log_file(date: str, limit: int = 1000, offset: int = 0) -> list[str]:
    """Read log file contents."""
    file_path = LOG_DIR / f"{date}.log"
    if not file_path.exists():
        return []

    lines = []
    with open(file_path, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
        lines = all_lines[offset:offset + limit]

    return [line.rstrip() for line in lines]


def export_logs_csv(date: str) -> str:
    """Export log file as CSV format."""
    lines = read_log_file(date, limit=10000)
    csv_lines = ["timestamp,level,message"]

    for line in lines:
        # Parse: "2026-01-27 10:30:00 [INFO] message"
        try:
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                timestamp = f"{parts[0]} {parts[1]}"
                rest = parts[2]
                if rest.startswith("[") and "]" in rest:
                    level = rest[1:rest.index("]")]
                    message = rest[rest.index("]") + 2:].replace('"', '""')
                    csv_lines.append(f'"{timestamp}","{level}","{message}"')
        except Exception:
            pass

    return "\n".join(csv_lines)
