from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from .client import get_client, LicenseError


def get_license_router(prefix: str = "") -> APIRouter:
    """
    Returns a FastAPI router exposing license-related APIs:

    - POST {prefix}/activate
    - GET  {prefix}/info
    - GET  {prefix}/status

    Example:
        app.include_router(get_license_router(prefix="/v1/license"))
    """
    router = APIRouter(prefix=prefix, tags=["license"])

    @router.post("/activate")
    async def license_activate(req: dict):
        """
        Proxy activation to license-agent.
        """
        try:
            return get_client().activate(
                license_key=req.get("license_key"),
                product_code=req.get("product_code"),
                fingerprint=req.get("fingerprint") or "node-1",
                version=req.get("version") or "0.0.0",
                vm_meta=req.get("vm_meta") or {},
            )
        except LicenseError as e:
            return JSONResponse(
                status_code=400,
                content={"detail": "activation_failed", "reason": str(e)},
            )

    @router.get("/info")
    async def license_info(license_key: str = Query(...)):
        """
        Proxy license info lookup to license-agent -> platform.
        """
        try:
            return get_client().license_info(license_key=license_key)
        except LicenseError as e:
            return JSONResponse(
                status_code=502,
                content={"ok": False, "detail": "lookup_failed", "reason": str(e)},
            )

    @router.get("/status")
    async def license_status():
        """
        Return local license status (used by UI and gate).
        """
        try:
            st = get_client().status()
            return {
                "active": st.active,
                "expired": st.expired,
                "in_grace": st.in_grace,
                "reason": st.reason,
                "contract_expires_at": st.contract_expires_at,
                "lease_expires_at": st.lease_expires_at,
            }
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"active": False, "detail": "license_check_failed", "reason": str(e)},
            )

    return router
