import logging
import os
import tempfile
from pathlib import Path

from utils.config_loader import BASE_DIR

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOG_FILE_ENV = "BATTEL_LOG_FILE"


def _resolve_log_file_path() -> Path:
    configured_path = os.environ.get(LOG_FILE_ENV, "").strip()
    if configured_path:
        return Path(configured_path).expanduser()
    return LOG_FILE


def setup_logger(name: str = "price_tracker") -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    requested_log_file = _resolve_log_file_path()
    try:
        requested_log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file_sink = logging.FileHandler(requested_log_file, encoding="utf-8")
    except OSError:
        fallback_log_file = Path(tempfile.gettempdir()) / "battel-app.log"
        log_file_sink = logging.FileHandler(fallback_log_file, encoding="utf-8")
    log_file_sink.setFormatter(formatter)

    console_sink = logging.StreamHandler()
    console_sink.setFormatter(formatter)

    logger.addHandler(log_file_sink)
    logger.addHandler(console_sink)
    return logger
