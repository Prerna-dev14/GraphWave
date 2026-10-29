"""Structured logging with correlation ID support and secret masking."""
import logging
import sys
import contextvars
from typing import Optional

correlation_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


class SafeLogFilter(logging.Filter):
    """Filters out sensitive credential strings from logs."""

    SENSITIVE_KEYS = ("api_key", "password", "secret", "authorization", "bearer")

    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.msg).lower()
        for key in self.SENSITIVE_KEYS:
            if f"{key}=" in msg or f'"{key}":' in msg:
                record.msg = "[REDACTED_SENSITIVE_DATA]"
                break
        record.correlation_id = correlation_id_ctx.get() or "no-trace"
        return True


def setup_logger(name: str = "graphweave", log_level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(SafeLogFilter())
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [trace=%(correlation_id)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger()
