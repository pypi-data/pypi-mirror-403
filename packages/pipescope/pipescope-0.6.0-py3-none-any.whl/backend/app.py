# PipeScope: Pipeline visualization for CPU microarchitecture traces
#
# Copyright (c) 2026 Microprocessor R&D Center (MPRC), Peking University
# SPDX-License-Identifier: MulanPSL-2.0
#
# Author: Chun Yang

"""FastAPI application entry point."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import Settings, CanvasTheme
from .trace import InstRec


def create_app(settings: Settings) -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title="PipeScope",
        description="Pipeline visualization for CPU microarchitecture traces",
        version=__version__,
    )

    # Load trace data
    all_insts = []
    with open(settings.trace_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            inst = InstRec.from_line(line)
            all_insts.append(inst)

    # Load canvas theme
    theme = CanvasTheme()

    # API routes
    #
    @app.get("/api/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "ok"}

    @app.get("/api/version")
    def get_version():
        """Get application version."""
        return {"version": __version__, "name": "PipeScope"}

    @app.get("/api/config")
    def get_config():
        """Get canvas configuration."""
        return {"canvasTheme": theme.to_dict()}

    @app.get("/api/trace")
    def get_trace():
        """Get all loaded trace data."""
        return [inst.to_dict() for inst in all_insts]

    # Serve static files (frontend)
    backend_dir = Path(__file__).parent
    app.mount(
        "/",
        StaticFiles(directory=str(backend_dir), html=True),
        name="frontend",
    )

    # Store settings in app state
    app.state.settings = settings
    app.state.all_insts = all_insts

    return app
