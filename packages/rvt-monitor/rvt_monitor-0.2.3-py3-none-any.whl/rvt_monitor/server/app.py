"""FastAPI application."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from rvt_monitor.server.routes import device, control, config, logs
from rvt_monitor.server.websocket import router as ws_router, status_update_loop
from rvt_monitor.server.state import ble_manager


class NoCacheMiddleware(BaseHTTPMiddleware):
    """Disable caching for static files during development."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

STATIC_DIR = Path(__file__).parent.parent / "static"

# Background task reference
_status_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global _status_task

    # Startup
    print("RVT-Monitor server starting...")

    # Start status update background task
    _status_task = asyncio.create_task(status_update_loop())

    yield

    # Shutdown
    print("RVT-Monitor server shutting down...")

    # Cancel background task
    if _status_task:
        _status_task.cancel()
        try:
            await _status_task
        except asyncio.CancelledError:
            pass

    # Disconnect BLE
    await ble_manager.disconnect()


app = FastAPI(
    title="RVT-Monitor",
    description="BLE Device Monitor Application",
    version="0.1.0",
    lifespan=lifespan,
)

# Add no-cache middleware for development
app.add_middleware(NoCacheMiddleware)

# Include routers
app.include_router(device.router, prefix="/api/device", tags=["device"])
app.include_router(control.router, prefix="/api/control", tags=["control"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(ws_router)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    """Serve main page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/stats")
async def stats():
    """Get command statistics."""
    return ble_manager.get_stats()
