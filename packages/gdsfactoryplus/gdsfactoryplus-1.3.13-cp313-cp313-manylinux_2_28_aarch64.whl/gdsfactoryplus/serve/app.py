"""GDSFactory+ Server Application."""

from __future__ import annotations

import asyncio
import contextlib
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

from doweb.browser import (
    get_app as _get_app,  # type: ignore[reportAttributeAccessIssue]
)
from doweb.layout_server import (
    LayoutViewServerEndpoint,  # type: ignore[reportAttributeAccessIssue]
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, RedirectResponse

from gdsfactoryplus import __version__, project, settings
from gdsfactoryplus import logger as log
from gdsfactoryplus.core import pdk
from gdsfactoryplus.core.communication import get_ws_port, ping_server, send_message
from gdsfactoryplus.models import (
    ReloadFactoriesMessage,
    ShutdownStatusMessage,
    StartupStatusMessage,
)
from gdsfactoryplus.registry import ServerInfo, ServerRegistry

__all__ = ["app"]
logger = log.get_logger()

logger.debug("app.py module loading...")

LayoutViewServerEndpoint.mode_dump = lambda _: ("ruler", "move instances")  # type: ignore[reportAttibuteAccessIssue]

THIS_DIR = Path(__file__).resolve().parent
GFP_DIR = THIS_DIR.parent

logger.debug("Getting settings...")
SETTINGS = settings.get_settings()
logger.debug("Settings loaded.")
PDK: str = SETTINGS["pdk"]["name"]
_msg = f"Using PDK: {PDK}"
logger.info(_msg)
logger.debug("Finding project dir...")
PROJECT_DIR = project.maybe_find_project_dir() or Path.cwd().resolve()
logger.debug("Project dir found.")
_msg = f"{PROJECT_DIR=}"
logger.info(_msg)
logger.debug("Creating FastAPI app...")

# Health check interval in seconds
HEALTH_CHECK_INTERVAL = 60

# Get HTTP port from environment (set by gfp-cli)
HTTP_PORT = int(os.getenv("GFP_HTTP_PORT", "8787"))


async def _health_check_loop() -> None:
    """Background task that pings VS Code websocket server periodically.

    If the ping fails, the server will shut down to avoid orphaned processes.
    """
    while True:
        await asyncio.sleep(HEALTH_CHECK_INTERVAL)
        result = ping_server()
        if result is False:  # Explicit False means ping failed
            logger.warning(
                "Health check failed: VS Code websocket server not responding"
            )
            logger.info("Shutting down server due to failed health check...")
            # Use os._exit to terminate immediately from async context
            # sys.exit() raises SystemExit which interferes with async cleanup
            os._exit(0)
        # result is None means no ws_port set (shouldn't happen here)
        # result is True means ping succeeded


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:  # noqa: PLR0915
    """Lifespan context manager for startup and shutdown events."""
    health_check_task: asyncio.Task[None] | None = None
    registry = ServerRegistry()

    try:
        # Startup
        ws_port = get_ws_port()
        if ws_port is not None:
            msg = f"Server using websocket port: {ws_port}"
            logger.info(msg)
        else:
            logger.info("No websocket port set, running standalone")

        # Register server in registry
        project_name = PROJECT_DIR.name
        server_info = ServerInfo(
            port=HTTP_PORT,
            pid=os.getpid(),
            project_path=str(PROJECT_DIR),
            project_name=project_name,
            pdk=PDK,
        )
        registry.register_server(server_info)
        logger.info(
            "Registered server on port %s for project '%s'", HTTP_PORT, project_name
        )

        send_message(
            StartupStatusMessage(
                message="Server startup successful. Just a moment please..."
            )
        )

        msg = f"Activating PDK: {PDK}"
        logger.info(msg)
        logger.debug("Calling pdk.get_pdk()...")
        pdk.get_pdk()
        logger.debug("pdk.get_pdk() completed.")
        try:
            logger.debug("Calling pdk.register_cells()...")
            pdk.register_cells()
            logger.debug("pdk.register_cells() completed.")
        except Exception as e:  # noqa: BLE001
            msg = f"Failed to register cells: {e}"
            logger.warning(msg)
            logger.warning("Creating new database due to previous error.")
            db_path = settings.get_db_path()
            db_path.unlink(missing_ok=True)
            pdk.register_cells()
        finally:
            send_message(ReloadFactoriesMessage())
            logger.info("Server running.")

        # Start health check background task only if ws_port is set
        if ws_port is not None:
            logger.info("Health checks enabled")
            health_check_task = asyncio.create_task(_health_check_loop())
        else:
            logger.info("Health checks disabled (no ws_port)")

        yield

    except Exception as e:
        msg = f"Server startup failed. {e}"
        logger.error(msg)  # noqa: TRY400
        send_message(
            ShutdownStatusMessage(message="Server startup failed. Please check logs...")
        )
        raise
    finally:
        # Cancel health check task if running
        if health_check_task is not None:
            health_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await health_check_task

        # Unregister server from registry
        registry.unregister_server(HTTP_PORT)
        logger.info("Unregistered server on port %s", HTTP_PORT)

        # Shutdown - always send shutdown message
        logger.info("Server stopped.")
        send_message(
            ShutdownStatusMessage(message="Server stopped. Please check logs...")
        )


app = cast("FastAPI", _get_app(fileslocation=str(PROJECT_DIR), editable=True))
logger.debug("FastAPI app created.")

# Modern way to set lifespan - replaces @app.on_event("startup")
app.router.lifespan_context = lifespan


def _needs_to_be_removed(path: str) -> bool:
    return path == "/" or path.startswith(("/file", "/gds"))


app.router.routes = [
    r for r in app.routes if not _needs_to_be_removed(getattr(r, "path", ""))
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def redirect() -> RedirectResponse:
    """Index should redirect to /code to make online workspaces open in code editor."""
    return RedirectResponse("/code/")


@app.get("/code")
def code() -> PlainTextResponse:
    """Dummy response which will be overwritten in online workspaces."""
    return PlainTextResponse("gfp server is running.")


@app.get("/info")
def info() -> dict[str, str | int]:
    """Get server information.

    Returns project metadata including port, PID, project path, and PDK.
    This endpoint is used by the MCP server to discover and connect to projects.

    Returns:
        Dictionary with server information
    """
    return {
        "project_name": PROJECT_DIR.name,
        "project_path": str(PROJECT_DIR),
        "port": HTTP_PORT,
        "pid": os.getpid(),
        "pdk": PDK,
        "version": __version__,
    }


def get_app() -> FastAPI:
    """Get the FastAPI app instance."""
    return app
