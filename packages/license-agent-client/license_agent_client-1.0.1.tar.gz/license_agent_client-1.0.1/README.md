# license-agent-client

A lightweight Python client and FastAPI helpers for enforcing licensing via a
local **license-agent** service.

This package is designed for applications such as **Logzy**, **MeyiConnect**,
or any product that uses a centralized licensing model:

```
Application → license-agent → license-platform
```

It eliminates duplicated license-handling code and provides a single,
consistent way to:

- Check license status
- Activate licenses
- Lookup license information
- Enforce license rules at API level
- Keep activation UI accessible while blocking product APIs


## Install

### Core client (no framework dependency)

```bash
pip install license-agent-client
```

### With FastAPI helpers (recommended)

```bash
pip install "license-agent-client[fastapi]"
```

---

## Environment variables

| Variable | Default | Description |
|--------|--------|-------------|
| LICENSE_AGENT_URL | `http://license-agent:8090` | Base URL of local license-agent |
| LICENSE_CACHE_SECONDS | `30` | Cache TTL (seconds) |
| LICENSE_TIMEOUT_SECONDS | `2` | HTTP timeout |
| REQUIRE_LICENSE | `false` | Enable license enforcement |

---

## Core usage (plain Python)

```python
from license_agent_client import get_client, LicenseInactiveError

client = get_client()

try:
    client.assert_active()
except LicenseInactiveError as e:
    print("License blocked:", e)
    raise SystemExit(1)
```

---

## FastAPI integration

```python
from fastapi import FastAPI
from license_agent_client.router import get_license_router
from license_agent_client.middleware import install_license_gate

app = FastAPI()

app.include_router(get_license_router(prefix="/v1/license"))
install_license_gate(app)
```

---

## License lifecycle behavior

| Platform action | Agent behavior | App behavior |
|---------------|---------------|--------------|
| Install | pending | blocked |
| Approved | activation allowed | unlocked |
| Deactivated | check-in fails | blocked |
| Rejected | new key allowed | reinstall |

---

## Block APIs when license is inactive (global gate)
from fastapi import FastAPI
from license_agent_client.middleware import install_license_gate

app = FastAPI()

install_license_gate(
    app,
    exempt_prefixes=(
        "/ui",
        "/health",
        "/v1/license",
    ),
)

## Typical FastAPI app layout
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from license_agent_client.router import get_license_router
from license_agent_client.middleware import install_license_gate

app = FastAPI()

# Serve activation UI
app.mount("/ui", StaticFiles(directory="/app/ui", html=True))

# License APIs
app.include_router(get_license_router(prefix="/v1/license"))

# Global license enforcement
install_license_gate(app)


## Fetch license limits
limits = get_client().limits()
print(limits)

## Activate a license (proxy to agent)
from license_agent_client import get_client

resp = get_client().activate(
    license_key="XXXX-YYYY-ZZZZ",
    product_code="logzy",
    fingerprint="node-1",
    version="1.2.3",
    vm_meta={"hostname": "prod-node-1"},
)

print(resp)

## License info lookup (proxy to agent → platform)
info = get_client().license_info(license_key="XXXX-YYYY-ZZZZ")
print(info)

## How apps use it (default UI)
from fastapi import FastAPI
from license_agent_client.ui import mount_default_ui
from license_agent_client.router import get_license_router
from license_agent_client.middleware import install_license_gate

app = FastAPI()

mount_default_ui(app)  # ✅ mounts built-in /ui
app.include_router(get_license_router(prefix="/v1/license"))
install_license_gate(app, exempt_prefixes=("/ui", "/health", "/v1/license"))


## How apps override it (custom UI)
from fastapi.staticfiles import StaticFiles

# override built-in UI
app.mount("/ui", StaticFiles(directory="/app/my-ui", html=True), name="custom-ui")


## License

MIT
