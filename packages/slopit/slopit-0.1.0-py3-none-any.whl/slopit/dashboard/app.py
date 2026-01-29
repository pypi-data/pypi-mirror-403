"""FastAPI application factory for slopit dashboard.

This module provides the application factory for creating and configuring
the slopit dashboard FastAPI application.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from slopit.dashboard.api import analysis, export, sessions, trials
from slopit.dashboard.config import DashboardConfig
from slopit.dashboard.websocket.handlers import handle_message
from slopit.dashboard.websocket.manager import ConnectionManager


def create_app(config: DashboardConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Parameters
    ----------
    config
        Dashboard configuration. Uses defaults if not provided.

    Returns
    -------
    FastAPI
        Configured FastAPI application instance.

    Examples
    --------
    >>> from slopit.dashboard import DashboardConfig
    >>> config = DashboardConfig(port=8080)
    >>> app = create_app(config)
    >>> print(app.title)
    Slopit Dashboard
    """
    if config is None:
        config = DashboardConfig()

    app = FastAPI(
        title="Slopit Dashboard",
        description="Analytics dashboard for AI response detection",
        version="0.1.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store config in app state
    app.state.config = config

    # WebSocket connection manager
    manager = ConnectionManager()
    app.state.ws_manager = manager

    # Include API routers
    app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
    app.include_router(trials.router, prefix="/api/v1/trials", tags=["trials"])
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
    app.include_router(export.router, prefix="/api/v1/export", tags=["export"])

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:  # pyright: ignore[reportUnusedFunction]
        """WebSocket endpoint for real-time updates.

        Accepts WebSocket connections and handles bidirectional
        communication for live session and analysis updates.
        """
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await handle_message(websocket, data, manager)
        except WebSocketDisconnect:
            await manager.disconnect(websocket)

    # Static files for React frontend (if exists)
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists() and any(static_dir.iterdir()):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app
