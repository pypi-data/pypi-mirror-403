"""Logging setup for algotrading-core."""

import io
import logging
import os
import sys
from datetime import datetime

_DEFAULT_LOG_FOLDER = "log"
_DEFAULT_LOG_LEVEL = logging.INFO


def _make_log_path(log_folder: str) -> str:
    """Build full path for today's log file.

    Args:
        log_folder: Directory to write log files into.

    Returns:
        Full path: log_folder/YYYY-MM-DD_HH-MM-SS.log
    """
    now = datetime.now()
    log_filename = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    return os.path.join(log_folder, log_filename)


def _create_formatter() -> logging.Formatter:
    """Create standard log formatter."""
    return logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def _add_handlers(
    logger: logging.Logger,
    log_path: str,
    log_level: int,
    formatter: logging.Formatter,
) -> None:
    """Add file and console handlers to root logger if none present.

    Args:
        logger: Root logger to configure.
        log_path: Full path for the log file.
        log_level: Level for handlers.
        formatter: Formatter for both handlers.
    """
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    if hasattr(sys.stdout, "buffer"):
        safe_stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
    else:
        safe_stdout = sys.stdout

    console_handler = logging.StreamHandler(safe_stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)


def setup_logger(
    log_folder: str = _DEFAULT_LOG_FOLDER,
    log_level: int = _DEFAULT_LOG_LEVEL,
) -> tuple[logging.Logger, str]:
    """Configure root logger with file and console handlers.

    Creates log_folder if it does not exist. Uses a timestamped log filename.
    Handlers are added only if the root logger has no handlers yet (idempotent).

    Args:
        log_folder: Directory for log files. Defaults to "log".
        log_level: Logging level (e.g. logging.INFO). Defaults to INFO.

    Returns:
        Tuple of (root logger, log filename only, e.g. "2025-01-29_12-00-00.log").
    """
    log_path = _make_log_path(log_folder)
    log_filename = os.path.basename(log_path)
    os.makedirs(log_folder, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(log_level)

    if not logger.handlers:
        formatter = _create_formatter()
        _add_handlers(logger, log_path, log_level, formatter)

    return logger, log_filename
