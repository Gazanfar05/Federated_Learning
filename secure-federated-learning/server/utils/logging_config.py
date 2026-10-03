from __future__ import annotations

import logging
from pathlib import Path

from server.config import settings


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    settings.log_dir.mkdir(parents=True, exist_ok=True)
    log_path = settings.log_dir / "server.log"
    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
