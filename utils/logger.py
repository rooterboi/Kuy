"""Logging sozlamasi: konsol + aylanuvchi .log fayl (admin paneldan ko'rish/o'chirish mumkin)."""
import logging
from logging.handlers import RotatingFileHandler

from config import LOG_FILE


def setup_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=1, encoding="utf-8")
    file_handler.setFormatter(fmt)
    console = logging.StreamHandler()
    console.setFormatter(fmt)

    root.addHandler(file_handler)
    root.addHandler(console)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
