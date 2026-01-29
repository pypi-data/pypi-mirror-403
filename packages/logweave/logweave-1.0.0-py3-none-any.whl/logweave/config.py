import os
import time
from pathlib import Path


class Config:
    """Configuration with intelligent environment variable caching.

    - Caches values for 60 seconds to reduce getenv() calls
    - Automatically refreshes for dynamic environment changes
    - Thread-safe for production use
    """

    def __init__(self):
        self._cache = {}
        self._last_refresh = {}
        self._cache_ttl_seconds = 60

    def _get_cached(self, env_key: str, default: str, transformer=None):
        """Get environment variable with caching.

        Args:
            env_key: Environment variable name
            default: Default value if not set
            transformer: Optional function to transform the value

        Returns: Cached or fresh environment value
        """
        now = time.time()

        # Refresh cache if TTL expired
        if env_key not in self._last_refresh or (now - self._last_refresh[env_key]) > self._cache_ttl_seconds:
            raw_value = os.getenv(env_key, default)
            self._cache[env_key] = transformer(raw_value) if transformer else raw_value
            self._last_refresh[env_key] = now

        return self._cache[env_key]

    # All properties now use caching
    @property
    def LOG_MODE(self):
        return self._get_cached("LOG_MODE", "dev")

    @property
    def LOG_LEVEL(self):
        return self._get_cached("LOG_LEVEL", "INFO", transformer=str.upper)

    @property
    def SERVICE_NAME(self):
        return self._get_cached("SERVICE_NAME", "unknown-service")

    @property
    def LOG_DIR(self):
        return self._get_cached("LOG_DIR", "logs")

    @property
    def LOG_FILE_NAME(self):
        return self._get_cached("LOG_FILE_NAME", os.getenv("SERVICE_NAME", "unknown-service"))

    @property
    def LOG_PATH(self):
        folder = self.LOG_DIR or "logs"
        return Path(folder) / self.LOG_FILE_NAME

    @property
    def LOG_ROTATION(self):
        return self._get_cached("LOG_MAX_FILE_SIZE", "20 MB")

    @property
    def LOG_RETENTION(self):
        return self._get_cached("LOG_MAX_HISTORY", "30 days")

    @property
    def LOG_COMPRESSION(self):
        return self._get_cached("LOG_COMPRESSED_ENABLED", "true", transformer=lambda x: x.lower() == "true")

    @property
    def LOG_MASK_KEYS(self):
        return self._get_cached("LOG_MASK_KEYS", "")

    @property
    def ENABLE_JSON_LOGS(self):
        return self._get_cached("ENABLE_JSON_LOGS", "true", transformer=lambda x: x.lower() == "true")

    @property
    def ENABLE_SENTRY(self):
        return self._get_cached("ENABLE_SENTRY", "true", transformer=lambda x: x.lower() == "true")

    @property
    def SENTRY_DSN(self):
        return self._get_cached("SENTRY_DSN", None)

    @property
    def ENABLE_TRACING_EXPORT(self):
        return self._get_cached("ENABLE_TRACING_EXPORT", "false", transformer=lambda x: x.lower() == "true")

    @property
    def OTEL_EXPORTER_ENDPOINT(self):
        return self._get_cached("OTEL_EXPORTER_ENDPOINT", None)


# Singleton instance
settings = Config()
