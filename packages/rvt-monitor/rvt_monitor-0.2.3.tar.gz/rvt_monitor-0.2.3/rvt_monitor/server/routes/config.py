"""Config API routes - dimension, torque, wifi."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from rvt_monitor.server.state import ble_manager

router = APIRouter()


class DimensionReadRequest(BaseModel):
    dimension_id: int


class DimensionWriteRequest(BaseModel):
    dimension_id: int
    value: int


class WiFiRequest(BaseModel):
    ssid: str
    password: str


@router.get("/dimension/{dimension_id}")
async def read_dimension(dimension_id: int):
    """Read a dimension value."""
    value = await ble_manager.read_dimension(dimension_id)
    if value is not None:
        return {
            "success": True,
            "dimension_id": dimension_id,
            "value": value,
        }
    return {
        "success": False,
        "error": "Failed to read dimension",
    }


@router.post("/dimension")
async def write_dimension(request: DimensionWriteRequest):
    """Write a dimension value."""
    success = await ble_manager.write_dimension(
        request.dimension_id,
        request.value,
    )
    return {"success": success}


@router.post("/dimension/save")
async def save_dimensions():
    """Save all dimensions to flash."""
    success = await ble_manager.save_dimensions()
    return {"success": success}


@router.post("/torque/reset")
async def reset_torque():
    """Reset torque model."""
    success = await ble_manager.reset_torque_model()
    return {"success": success}


@router.post("/torque/save")
async def save_torque():
    """Save torque model."""
    success = await ble_manager.save_torque_model()
    return {"success": success}


@router.post("/wifi")
async def set_wifi(request: WiFiRequest):
    """Set WiFi configuration."""
    success = await ble_manager.set_wifi_config(request.ssid, request.password)
    return {"success": success}
