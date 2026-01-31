"""Device API routes - scan, connect, disconnect, status."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rvt_monitor.ble.scanner import scan_devices
from rvt_monitor.server.state import app_state, ble_manager

router = APIRouter()


class ConnectRequest(BaseModel):
    address: str
    name: str = ""


@router.get("/devices")
async def get_devices():
    """Get cached device list (no scan)."""
    return {
        "success": True,
        "devices": app_state.scanned_devices,
        "last_scan": (
            app_state.last_scan_time.isoformat()
            if app_state.last_scan_time else None
        ),
    }


@router.get("/scan")
async def scan():
    """Scan for BLE devices and cache results."""
    try:
        devices = await scan_devices(timeout=5.0)
        # Cache results
        app_state.scanned_devices = [d.to_dict() for d in devices]
        app_state.last_scan_time = datetime.now()
        return {
            "success": True,
            "devices": app_state.scanned_devices,
            "last_scan": app_state.last_scan_time.isoformat(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "devices": app_state.scanned_devices,  # Return cached on error
        }


@router.post("/connect")
async def connect(request: ConnectRequest):
    """Connect to a BLE device."""
    try:
        success = await ble_manager.connect(request.address, request.name)
        return {
            "success": success,
            "device_name": ble_manager.device_name,
            "device_type": ble_manager.device_type,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/disconnect")
async def disconnect():
    """Disconnect from current device."""
    try:
        await ble_manager.disconnect()
        return {"success": True}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/status")
async def get_status():
    """Get current connection status and device info."""
    info = ble_manager.get_connection_info()  # device_info included if connected

    if ble_manager.connected:
        status = await ble_manager.read_status()
        if status:
            info["status"] = status.to_dict()

    # Include cached device list
    info["devices"] = app_state.scanned_devices
    info["last_scan"] = (
        app_state.last_scan_time.isoformat()
        if app_state.last_scan_time else None
    )

    return info


@router.get("/device-info")
async def get_device_info():
    """Read Device Information Service (BLE SIG 0x180A).

    Returns model_number, hardware_revision, firmware_revision, protocol_version.
    """
    if not ble_manager.connected:
        raise HTTPException(status_code=400, detail="Not connected to device")

    try:
        device_info = await ble_manager.read_device_info()
        if device_info:
            return {
                "success": True,
                **device_info,
            }
        return {
            "success": False,
            "error": "Failed to read device info",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
