"""Logging setup for Horizon Data Pipelines."""

import functools
import logging
import sys
import time
from collections.abc import Callable
from typing import Final, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def log_calls(logger: logging.Logger, level: int = logging.INFO) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Log function entry and exit with a correlation ID.

    Args:
        logger: The logger instance to use
        level: Logging level (e.g., logging.INFO, logging.DEBUG)

    Example:
        >>> logger = logging.getLogger(__name__)
        >>> @log_calls(logger, logging.DEBUG)
        ... def my_function(x: int, y: int) -> int:
        ...     return x + y
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Use timestamp as correlation ID
            call_id = int(time.time() * 1_000_000) % 1_000_000_000

            # Log entry - let logger do the formatting
            logger.log(level, "→ ENTER [%s] %s", call_id, func.__name__)

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                # Log exception exit
                logger.log(level, "✗ ERROR [%s] %s raised %s: %s", call_id, func.__name__, type(e).__name__, e)
                raise
            else:
                # Log successful exit
                logger.log(level, "← EXIT  [%s] %s", call_id, func.__name__)
                return result

        return wrapper

    return decorator


def setup_extra_logger() -> logging.Logger:
    """Set up the root logger for extra fields."""
    # Create a handler for the standard output
    hnd = logging.StreamHandler(sys.stdout)
    # Set the formatter to our formatter than handles "extra" fields
    hnd.setFormatter(ExFormatter("%(name)s - %(levelname)s - %(message)s"))
    # Get the root logger
    logger = logging.getLogger()
    # Clear any existing handlers to avoid duplicates on stdout
    logger.handlers.clear()
    # Add the new handler to the root logger
    logger.addHandler(hnd)
    return logger


__all__ = ["setup_extra_logger"]


class ExFormatter(logging.Formatter):
    def_keys: Final[list[str]] = [
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
    ]

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record."""
        string = super().format(record)
        extra = {k: v for k, v in record.__dict__.items() if k not in self.def_keys}
        if len(extra) > 0:
            string += " - extra: " + str(extra)
        return string
