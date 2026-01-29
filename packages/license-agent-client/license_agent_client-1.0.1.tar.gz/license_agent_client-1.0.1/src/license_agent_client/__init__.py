"""license-agent-client.

Core:
- LicenseClient: HTTP client to a local license-agent.
- LicenseStatus + errors.

Optional FastAPI helper:
- license_agent_client.fastapi.require_active_license
"""

from .client import LicenseClient, LicenseStatus, LicenseError, LicenseInactiveError, get_client

__all__ = [
    "LicenseClient",
    "LicenseStatus",
    "LicenseError",
    "LicenseInactiveError",
    "get_client",
]
