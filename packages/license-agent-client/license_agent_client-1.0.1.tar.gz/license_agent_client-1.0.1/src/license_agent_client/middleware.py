from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request

from .client import get_client, LicenseInactiveError
from .config import require_license


def install_license_gate(
    app: FastAPI,
    *,
    exempt_prefixes: tuple[str, ...] = ("/ui", "/health", "/v1/license"),
):
    """
    Install a global license gate middleware.

    Behavior:
    - If REQUIRE_LICENSE=false → no-op
    - Exempt paths (UI, activation, health) always allowed
    - Inactive/expired license → 402
    - License-agent unreachable → 503 (fail-closed)
    """

    @app.middleware("http")
    async def license_gate(request: Request, call_next):
        if not require_license():
            return await call_next(request)

        for prefix in exempt_prefixes:
            if request.url.path.startswith(prefix):
                return await call_next(request)

        try:
            get_client().assert_active()
        except LicenseInactiveError as e:
            return JSONResponse(
                status_code=402,
                content={"detail": "license_required", "reason": str(e)},
            )
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"detail": "license_check_failed", "reason": str(e)},
            )

        return await call_next(request)
