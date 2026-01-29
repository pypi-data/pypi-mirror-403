import inspect
import logging

from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Generic standard library logging handler that redirects all logs to Loguru.
    Ensures third-party logs (Uvicorn, etc.) are processed by LogWeave.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = inspect.currentframe(), 0
            try:
                while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
                    frame = frame.f_back
                    depth += 1
            finally:
                del frame  # CRITICAL: Prevent frame reference memory leak

            logger.opt(depth=depth, exception=record.exc_info).bind(
                logger=record.name  # This captures "uvicorn.access" or "sqlalchemy.engine"
            ).log(level, record.getMessage())
        except Exception:
            # Handler must NEVER raise (standard library logging requirement)
            self.handleError(record)
