from __future__ import annotations

import os


def _to_bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def license_agent_url(default: str = "http://license-agent:8090") -> str:
    return os.getenv("LICENSE_AGENT_URL", default).strip() or default


def license_cache_seconds(default: int = 30) -> int:
    v = os.getenv("LICENSE_CACHE_SECONDS")
    try:
        return int(v) if v is not None else default
    except Exception:
        return default


def license_timeout_seconds(default: float = 2.0) -> float:
    v = os.getenv("LICENSE_TIMEOUT_SECONDS")
    try:
        return float(v) if v is not None else float(default)
    except Exception:
        return float(default)


def require_license(default: bool = False) -> bool:
    return _to_bool(os.getenv("REQUIRE_LICENSE"), default=default)
