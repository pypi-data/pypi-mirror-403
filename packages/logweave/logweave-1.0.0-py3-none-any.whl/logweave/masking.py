import re

from logweave.config import settings

_PATTERN_CACHE = {}


def _get_mask_pattern(key: str):
    """Get cached regex pattern for masking a specific key."""
    if key not in _PATTERN_CACHE:
        _PATTERN_CACHE[key] = re.compile(
            rf'("{re.escape(key)}"\s*:\s*|{re.escape(key)}\s*[:=]\s*)["\']?([^"\'\s,}}]+)["\']?', re.IGNORECASE
        )
    return _PATTERN_CACHE[key]


# ---------------------------------------------------------------------
# Robust Regex Pattern
# ---------------------------------------------------------------------
# This pattern matches: "key": "val", 'key': 'val', key=val, key: val
def get_mask_pattern(key: str):
    return re.compile(
        rf'({re.escape(key)}\s*[:=]\s*["\']?)[^"\'\s,}}]+(["\']?)',
        re.IGNORECASE,
    )


def mask_sensitive_data(message: str) -> str:
    if not message or not isinstance(message, str):
        return message

    # Dynamically fetch keys so monkeypatch works
    extra_keys = [k.strip() for k in settings.LOG_MASK_KEYS.split(",") if k.strip()]
    keys_to_mask = ["password", "token", "secret"] + extra_keys

    for key in keys_to_mask:
        pattern = _get_mask_pattern(key)  # Use cached pattern
        message = pattern.sub(r"\1****", message)

    return message
