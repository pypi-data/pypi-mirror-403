from __future__ import annotations

import inspect
from typing import Any

from loguru import logger as loguru_logger

from logweave.config import settings
from logweave.trace_context import get_trace_context


class LogWeaveLogger:
    """
    Enterprise logging facade (SLF4J-style).
    Application code MUST use this only.
    """

    def __init__(self, name: str):
        self.name = name

        # Bind static context ONCE
        self._logger = loguru_logger.bind(
            logger=name,
            service=settings.SERVICE_NAME,
        )

        # ADD THESE: Cache trace context
        self._last_trace_id = None
        self._last_span_id = None
        self._cached_logger = None

    # ---------------------------
    # Helpers
    # ---------------------------

    def _format(self, msg: str, *args: Any) -> str:
        if not args:
            return msg
        try:
            return msg.format(*args)
        except Exception:
            return msg

    def _get_or_bind_trace(self):
        """Get trace-bound logger, reusing if context hasn't changed.

        Avoids ~80-90% of bind() calls by reusing logger when trace context is stable.
        """
        trace_id, span_id = get_trace_context()

        #  Only rebind if trace context actually changed
        if trace_id != self._last_trace_id or span_id != self._last_span_id:
            self._last_trace_id = trace_id
            self._last_span_id = span_id
            self._cached_logger = self._logger.bind(
                trace_id=trace_id,
                span_id=span_id,
            )

        # Return cached logger (reused across multiple logs in same context)
        return self._cached_logger or self._logger

    # ---------------------------
    # Public API
    # ---------------------------

    def info(self, msg: str, *args: Any):
        logger = self._get_or_bind_trace()
        logger.info(self._format(msg, *args))

    def debug(self, msg: str, *args: Any):
        logger = self._get_or_bind_trace()
        logger.debug(self._format(msg, *args))

    def warning(self, msg: str, *args: Any):
        logger = self._get_or_bind_trace()
        logger.warning(self._format(msg, *args))

    def warn(self, msg: str, *args: Any):
        self.warning(msg, *args)

    def error(self, msg: str, *args: Any, exc: Exception | None = None):
        logger = self._get_or_bind_trace()
        if exc:
            logger.exception(self._format(msg, *args))
        else:
            logger.error(self._format(msg, *args))


class LoggerFactory:
    """
    SLF4J-style LoggerFactory.
    """

    @staticmethod
    def getLogger(name: str | None = None) -> LogWeaveLogger:
        if not name:
            frame = inspect.stack()[1]
            name = frame.frame.f_globals.get("__name__", "unknown")
        return LogWeaveLogger(name)
