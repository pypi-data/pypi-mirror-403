from __future__ import annotations

"""FastAPI helper to enforce an active license via local license-agent."""

from .client import get_client, LicenseInactiveError
from .config import require_license

try:
    from fastapi import HTTPException
except Exception:  # pragma: no cover
    HTTPException = None  # type: ignore


def require_active_license() -> None:
    """Block request if REQUIRE_LICENSE=true and license is inactive/unreachable."""
    if not require_license():
        return

    if HTTPException is None:  # pragma: no cover
        raise RuntimeError("fastapi is not installed. Install: license-agent-client[fastapi]")

    try:
        get_client().assert_active()
    except LicenseInactiveError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except Exception:
        raise HTTPException(status_code=503, detail="License service unavailable")
