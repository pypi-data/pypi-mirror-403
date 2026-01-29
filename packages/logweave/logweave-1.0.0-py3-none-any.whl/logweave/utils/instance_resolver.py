from __future__ import annotations

import os
import socket


def _get_env_instance_id() -> str | None:
    """
    Highest priority: explicit user-provided instance ID.
    """
    return os.getenv("INSTANCE_ID")


def _get_container_id() -> str | None:
    """
    Try to extract Docker / Kubernetes container ID.
    Works on most Linux container runtimes.
    """
    try:
        with open("/proc/self/cgroup", encoding="utf-8") as f:
            for line in f:
                # Docker / containerd style IDs
                if "docker" in line or "containerd" in line:
                    parts = line.strip().split("/")
                    container_id = parts[-1]
                    if len(container_id) >= 12:
                        return container_id[:12]
    except Exception:
        pass

    return None


def _get_hostname() -> str | None:
    """
    Stable hostname-based identifier.
    """
    try:
        return socket.gethostname()
    except Exception:
        return None


def _get_pid() -> str:
    """
    Last-resort fallback. Always available.
    """
    return f"pid-{os.getpid()}"


def resolve_instance_id() -> str:
    """
    Resolve instance_id using 'auto' strategy.

    Priority:
    1. INSTANCE_ID env var
    2. Container ID
    3. Hostname
    4. PID fallback
    """

    return _get_env_instance_id() or _get_container_id() or _get_hostname() or _get_pid()


def build_file_suffix(instance_id: str) -> str:
    """
    Build filename-safe suffix for log files.

    Example:
        instance_id = "pid-1234"
        -> ".pid-1234"
    """
    return f".{instance_id}"
