from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, TextIO

try:
    from .app_paths import default_log_path
except ImportError:
    from app_paths import default_log_path


LOGGER_NAME = "CDDA_editor"
DEFAULT_LOG_PATH = default_log_path()


class ReopeningFileHandler(logging.Handler):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self.terminator = "\n"

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(message)
            f.write(self.terminator)


def configure_app_logging(
    log_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
    console_stream: Optional[TextIO] = None,
    force: bool = False,
) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers and not force:
        return logger

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(console_stream or sys.stderr)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)

    resolved_log_path = Path(log_path) if log_path is not None else default_log_path(base_dir)
    resolved_log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = ReopeningFileHandler(resolved_log_path)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    logger.info("Logging initialized: %s", resolved_log_path)
    return logger
