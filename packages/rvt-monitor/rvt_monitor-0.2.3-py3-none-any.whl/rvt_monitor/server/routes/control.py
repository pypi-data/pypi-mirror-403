"""Control API routes - motion commands, LED control."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from rvt_monitor.ble.protocol import LEDTarget
from rvt_monitor.server.state import ble_manager

router = APIRouter()


class CommandRequest(BaseModel):
    action: str  # up, down, stop, open, close


class LEDRequest(BaseModel):
    command: str  # brightness, color_index
    target: int = 0  # 0=main, 1=head, 3=mood
    value: int = 0


@router.post("/command")
async def send_command(request: CommandRequest):
    """Send motion command."""
    action = request.action.lower()

    if action in ("up", "open"):
        success = await ble_manager.send_up()
    elif action in ("down", "close"):
        success = await ble_manager.send_down()
    elif action == "stop":
        success = await ble_manager.send_stop()
    else:
        return {
            "success": False,
            "error": f"Unknown action: {action}",
        }

    return {"success": success}


@router.post("/led")
async def set_led(request: LEDRequest):
    """Set LED settings."""
    command = request.command.lower()

    try:
        target = LEDTarget(request.target)
    except ValueError:
        target = LEDTarget.MAIN

    if command == "brightness":
        success = await ble_manager.set_led_brightness(target, request.value)
    elif command == "color_index":
        success = await ble_manager.set_led_color_index(request.value)
    else:
        return {
            "success": False,
            "error": f"Unknown LED command: {command}",
        }

    return {"success": success}
