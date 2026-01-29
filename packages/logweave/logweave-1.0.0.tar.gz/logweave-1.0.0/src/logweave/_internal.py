import json
import logging
import socket
import sys
import time
import traceback

import structlog
from loguru import logger

from logweave.config import settings
from logweave.interceptor_handler import InterceptHandler
from logweave.masking import mask_sensitive_data
from logweave.trace_context import get_trace_context

#  Hostname cache with TTL
_HOSTNAME_CACHE = {
    "value": None,
    "timestamp": None,
    "ttl_seconds": 300,  # Refresh every 5 minutes
}

# Template strings precomputed at module load time
_CONSOLE_FORMAT_TEMPLATE = (
    "<green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> | "
    "<level>{{level:<8}}</level> | "
    "<cyan>{service}</cyan> | "
    "[<bold>{thread}</bold>] | "
    "<cyan>{logger_name}</cyan> :: "
    "tid=<magenta>{trace_id}</magenta> :: "
    "{{message}}"
)

_HUMAN_FORMAT_TEMPLATE = (
    "<green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> | "
    "<level>{{level:<8}}</level> | "
    "<cyan>{service}</cyan> | "
    "[<bold>{thread}</bold>] | "
    "<cyan>{logger_name}</cyan> :: "
    "tid=<magenta>{trace_id}</magenta> sid=<magenta>{span_id}</magenta> :: "
    "{{message}}"
)


# Lazy-load hostname to support dynamic environments (containers, etc.)
def _get_hostname():
    """Get hostname with intelligent caching.

    Returns cached value if fresh (<5 minutes old).
    Refreshes automatically for dynamic environments (containers).
    """
    now = time.time()

    # Return cached value if still fresh
    if (
        _HOSTNAME_CACHE["value"]
        and _HOSTNAME_CACHE["timestamp"]
        and now - _HOSTNAME_CACHE["timestamp"] < _HOSTNAME_CACHE["ttl_seconds"]
    ):
        return _HOSTNAME_CACHE["value"]

    # Fetch fresh hostname (happens once per 5 minutes)
    try:
        hostname = socket.gethostname()
        _HOSTNAME_CACHE["value"] = hostname
        _HOSTNAME_CACHE["timestamp"] = now
        return hostname
    except Exception:
        return _HOSTNAME_CACHE["value"] or "unknown-host"


# ---------------------------------------------------------------------
# Human-readable formatter (For .log files - Includes Traceback)
# ---------------------------------------------------------------------
def console_formatter(record):
    """Format for console output with optimized string handling."""
    extra = record["extra"]

    # Single format() call instead of multiple f-strings
    fmt = _CONSOLE_FORMAT_TEMPLATE.format(
        service=extra.get("service", "unknown"),
        thread=record["thread"].name,
        logger_name=extra.get("logger", record["name"]),
        trace_id=extra.get("trace_id", "no-trace"),
    )

    if record["exception"]:
        exc_type, exc_value, _ = record["exception"]
        # Single replace operation with pre-escaped value
        safe_exc_msg = str(exc_value).replace("{", "[").replace("}", "]")
        error_summary = f"<red><bold>{exc_type.__name__}: <italic>{safe_exc_msg}</italic></bold></red>"
        fmt += f"\n {error_summary}"

    return fmt + "\n"


def human_formatter(record):
    """Format for human-readable log files with optimized string handling."""
    extra = record["extra"]

    fmt = _HUMAN_FORMAT_TEMPLATE.format(
        service=extra.get("service", "unknown"),
        thread=record["thread"].name,
        logger_name=extra.get("logger", record["name"]),
        trace_id=extra.get("trace_id", "-"),
        span_id=extra.get("span_id", "-"),
    )

    if record["exception"]:
        fmt += "\n{exception}\n"

    return fmt


# ---------------------------------------------------------------------
# JSON formatter (Machine-readable - Full Stack Trace)
# ---------------------------------------------------------------------
def json_formatter(record):
    extra = record["extra"]

    payload = {
        "@timestamp": record["time"].isoformat(),
        "log.level": record["level"].name,
        "service.name": extra.get("service", "unknown-service"),
        "message": record["message"],
        "log.logger": extra.get("logger", record["name"]),
        "trace.id": extra.get("trace_id", "-"),
        "span.id": extra.get("span_id", "-"),
        "process.thread.name": record["thread"].name,
        "host.hostname": _get_hostname(),
    }

    if record["exception"]:
        exc_type, exc_value, exc_tb = record["exception"]
        try:
            st_trace = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

            payload["error"] = {
                "type": getattr(exc_type, "__name__", "Exception"),
                "message": str(exc_value),
                "stack_trace": st_trace,
            }

            if hasattr(exc_value, "errors") and callable(exc_value.errors):
                payload["error"]["details"] = exc_value.errors()
        finally:
            # CRITICAL: Prevent traceback object memory leak
            # Traceback objects hold references to all local variables in every frame
            del exc_type, exc_value, exc_tb

    reserved = {"service", "logger", "trace_id", "span_id", "serialized"}
    for key, value in extra.items():
        if key not in reserved:
            payload.setdefault("labels", {})[key] = value

    record["extra"]["serialized"] = json.dumps(payload, default=str)
    return "{extra[serialized]}\n"


# ---------------------------------------------------------------------
# structlog → Loguru bridge
# ---------------------------------------------------------------------
def structlog_to_loguru(_, __, event_dict):
    """
     Final structlog processor.
    Converts structured event → Loguru log call.
    """
    level = event_dict.pop("level", "info").upper()
    message = event_dict.pop("message", "")

    # Inject required fields if they are missing
    if "logger" not in event_dict:
        event_dict["logger"] = "structlog.internal"

    if "trace_id" not in event_dict or "span_id" not in event_dict:
        trace_id, span_id = get_trace_context()
        event_dict.setdefault("trace_id", trace_id)
        event_dict.setdefault("span_id", span_id)

    # Use depth=2 so Loguru correctly identifies the caller outside the bridge
    logger.opt(depth=2).log(level, message, **event_dict)
    return event_dict


# --- 1. The Global Patching Function ---
def global_masker(record):
    """
    This function runs on EVERY log record created by Loguru.
    It redacts sensitive data before the log hits any file or console.
    """
    record["message"] = mask_sensitive_data(record["message"])
    return True  # Always return True so the log is not dropped


# ---------------------------------------------------------------------
# Logging setup (framework entry)
# ---------------------------------------------------------------------
def setup_logging():
    """
    Configure LogWeave logging backend.

    - Loguru handles IO, rolling, retention, async
    - structlog builds structured events
    """

    # 1. Start with a clean state and apply the global patch
    logger.remove()

    # 2. UPDATED: Define custom colors and bold styling for each level
    # These must be set before adding handlers for the <level> tag to work
    # 2026 Corrected Industry Standard Bold Colors for Loguru
    logger.level("TRACE", color="<dim><bold>")
    logger.level("DEBUG", color="<blue><bold>")
    logger.level("INFO", color="<cyan><bold>")
    logger.level("SUCCESS", color="<green><bold>")
    logger.level("WARNING", color="<yellow><bold>")
    logger.level("ERROR", color="<red><bold>")
    logger.level("CRITICAL", color="<white><bold><bg red>")

    # 3. Fetch values dynamically from the settings object
    log_path = settings.LOG_PATH
    file_name = settings.LOG_FILE_NAME

    # 2. Ensure the directory exists (not the file path itself)
    log_path.mkdir(parents=True, exist_ok=True)

    # Remove all default handlers

    # ---------------- Console ----------------
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=console_formatter,
        colorize=True,  # Force color support for terminal
        filter=global_masker,  # <--- Apply masking here
        enqueue=True,
        # backtrace=True,
        # diagnose=False,
    )

    is_dev = settings.LOG_MODE == "dev"

    # ---------------- Human log file ----------------
    log_file_path = log_path / f"{file_name}.log"
    logger.add(
        log_file_path,
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="gz" if settings.LOG_COMPRESSION else None,
        format=human_formatter,
        colorize=False,  # Ensure no ANSI codes in text files
        filter=global_masker,  # <--- Apply masking here
        enqueue=True,
        backtrace=True,
        diagnose=is_dev,
    )

    # ---------------- JSON log file ----------------
    log_json_file_path = log_path / f"{file_name}.json.log"
    if settings.ENABLE_JSON_LOGS:
        logger.add(
            log_json_file_path,
            level=settings.LOG_LEVEL,
            rotation=settings.LOG_ROTATION,
            retention=settings.LOG_RETENTION,
            compression="gz" if settings.LOG_COMPRESSION else None,
            format=json_formatter,  # formatter, not sink
            filter=global_masker,  # <--- Apply masking here
            enqueue=True,
            backtrace=True,
            diagnose=is_dev,
        )

    # ---------------- structlog configuration ----------------
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.EventRenamer("message"),
            structlog_to_loguru,  # ← THE BRIDGE
        ],
        logger_factory=structlog.ReturnLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 1. The Generic Interceptor (Attach only once to the root)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 2. Silence the specific third-party loggers that are too noisy
    # Industry standard: Let logs propagate but remove their default handlers
    # to avoid double-printing in the console.
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
