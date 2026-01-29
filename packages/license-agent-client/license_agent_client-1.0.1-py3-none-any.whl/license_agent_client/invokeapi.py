from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from license_agent_client import get_client, LicenseError

router = APIRouter()

@router.post("/v1/license/activate")
async def license_activate(req):
    try:
        return get_client().activate(
            license_key=req.license_key,
            product_code=req.product_code,
            fingerprint=req.fingerprint or "node-1",
            version=req.version or "0.0.0",
            vm_meta=req.vm_meta or {},
        )
    except LicenseError as e:
        return JSONResponse({"detail": "activation_failed", "reason": str(e)}, status_code=400)

@router.get("/v1/license/info")
async def license_info(license_key: str = Query(...)):
    try:
        return get_client().license_info(license_key=license_key)
    except LicenseError as e:
        return JSONResponse({"ok": False, "detail": "lookup_failed", "reason": str(e)}, status_code=502)
