from __future__ import annotations

import importlib.resources as pkg_resources
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI

def mount_default_ui(app: FastAPI, mount_path: str = "/ui") -> None:
    """
    Mount the package's built-in activation UI at /ui.

    Apps can override by mounting their own StaticFiles at the same path.
    """
    # FastAPI StaticFiles expects a filesystem directory.
    # importlib.resources provides a Traversable; StaticFiles supports path-like only.
    # So we resolve to a real path via as_file().
    ui_pkg = pkg_resources.files("license_agent_client").joinpath("ui")
    with pkg_resources.as_file(ui_pkg) as ui_dir:
        app.mount(mount_path, StaticFiles(directory=str(ui_dir), html=True), name="license-ui")
