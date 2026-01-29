"""Logging setup for codegen."""

import logging
from typing import ClassVar


class ColorFormatter(logging.Formatter):
    """Color formatter for logging."""

    COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record."""
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter("%(levelname)s - %(message)s"))
    logging.root.addHandler(handler)
    logging.root.setLevel(level)
