from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional

from . import config


class LicenseError(Exception):
    """Base error for license-agent-client."""


class LicenseInactiveError(LicenseError):
    """Raised when the license is not active (expired/deactivated/etc.)."""


@dataclass(frozen=True)
class LicenseStatus:
    active: bool
    expired: bool
    in_grace: bool
    reason: str | None = None
    contract_expires_at: str | None = None
    lease_expires_at: str | None = None


class LicenseClient:
    def __init__(
        self,
        base_url: str,
        cache_seconds: int = 30,
        timeout_seconds: float = 2.0,
        user_agent: str = "license-agent-client/0.2.0",
    ):
        self.base_url = base_url.rstrip("/")
        self.cache_seconds = max(0, int(cache_seconds))
        self.timeout_seconds = float(timeout_seconds)
        self.user_agent = user_agent

        self._cached_at: float = 0.0
        self._cached_status: Optional[LicenseStatus] = None
        self._cached_limits: Optional[Dict[str, Any]] = None

    @classmethod
    def from_env(
        cls,
        *,
        default_base_url: str = "http://license-agent:8090",
        default_cache_seconds: int = 30,
        default_timeout_seconds: float = 2.0,
    ) -> "LicenseClient":
        return cls(
            base_url=config.license_agent_url(default_base_url),
            cache_seconds=config.license_cache_seconds(default_cache_seconds),
            timeout_seconds=config.license_timeout_seconds(default_timeout_seconds),
        )

    def _request_json(self, method: str, path: str, body: Optional[dict] = None) -> Any:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, method=method, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            # keep agent's payload if it's JSON, else raw text
            try:
                payload = json.loads(raw) if raw else {}
            except Exception:
                payload = raw
            raise LicenseError(f"HTTP {e.code} from license-agent: {payload}") from None
        except Exception as e:
            raise LicenseError(f"Failed to reach license-agent at {url}: {type(e).__name__} {e}") from None

        try:
            return json.loads(raw) if raw else {}
        except Exception as e:
            raise LicenseError(f"Invalid JSON from license-agent: {type(e).__name__} {e}; body={raw!r}") from None

    # existing methods now use _request_json
    def status(self, *, force: bool = False) -> LicenseStatus:
        now = time.time()
        if (not force) and self._cached_status and (now - self._cached_at) < self.cache_seconds:
            return self._cached_status

        data = self._request_json("GET", "/local/status")
        st = LicenseStatus(
            active=bool(data.get("active")),
            expired=bool(data.get("expired")),
            in_grace=bool(data.get("in_grace")),
            reason=data.get("reason"),
            contract_expires_at=data.get("contract_expires_at"),
            lease_expires_at=data.get("lease_expires_at"),
        )
        self._cached_at = now
        self._cached_status = st
        return st

    def limits(self, *, force: bool = False) -> Dict[str, Any]:
        now = time.time()
        if (not force) and self._cached_limits is not None and (now - self._cached_at) < self.cache_seconds:
            return self._cached_limits

        data = self._request_json("GET", "/local/limits")
        self._cached_limits = data.get("limits") or {}
        self._cached_at = now
        return self._cached_limits

    def assert_active(self) -> None:
        st = self.status()
        if st.active:
            return
        if st.expired and st.in_grace:
            return
        raise LicenseInactiveError(st.reason or "License inactive")

    def activate(
        self,
        *,
        license_key: str,
        product_code: str,
        fingerprint: str = "node-1",
        version: str = "0.0.0",
        vm_meta: Optional[dict] = None,
    ) -> Dict[str, Any]:
        payload = {
            "license_key": license_key,
            "product_code": product_code,
            "fingerprint": fingerprint,
            "version": version,
            "vm_meta": vm_meta or {},
        }
        return self._request_json("POST", "/local/activate", payload)

    def license_info(self, *, license_key: str) -> Dict[str, Any]:
        q = urllib.parse.quote(license_key, safe="")
        return self._request_json("GET", f"/local/license-info?license_key={q}")


_client_singleton: Optional[LicenseClient] = None


def get_client() -> LicenseClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = LicenseClient.from_env()
    return _client_singleton
