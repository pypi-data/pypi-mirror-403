"""WebSocket handler for real-time updates with controller lock."""

import asyncio
import json
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from rvt_monitor.server.state import app_state, ble_manager, ActivationTier
from rvt_monitor.ble.profiles import get_profile

router = APIRouter()

# Connected WebSocket clients: client_id -> WebSocket
clients: Dict[str, WebSocket] = {}

# Background task reference
_status_task: Optional[asyncio.Task] = None


async def broadcast(message: dict, exclude_id: Optional[str] = None):
    """Broadcast message to all connected clients."""
    if not clients:
        return

    text = json.dumps(message)
    disconnected = []

    for client_id, ws in clients.items():
        if client_id == exclude_id:
            continue
        try:
            await ws.send_text(text)
        except Exception:
            disconnected.append(client_id)

    # Clean up disconnected clients
    for client_id in disconnected:
        clients.pop(client_id, None)
        app_state.remove_client(client_id)


async def send_to_client(client_id: str, message: dict):
    """Send message to a specific client."""
    ws = clients.get(client_id)
    if ws:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            pass


async def broadcast_status(include_devices: bool = False):
    """Broadcast current device status to all clients."""
    info = ble_manager.get_connection_info()
    stats = ble_manager.get_stats()
    state_info = app_state.get_state_info()

    if ble_manager.connected and ble_manager.status:
        info["status"] = ble_manager.status.to_dict()

    info["stats"] = stats
    info["app_state"] = state_info

    # Only include device list on initial connection or explicit request
    if include_devices:
        info["devices"] = app_state.scanned_devices
        info["last_scan"] = (
            app_state.last_scan_time.isoformat()
            if app_state.last_scan_time else None
        )

    await broadcast({
        "type": "status",
        "data": info,
    })


async def broadcast_log(level: str, message: str):
    """Broadcast log message to all clients."""
    await broadcast({
        "type": "log",
        "data": {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
        },
    })


async def broadcast_lock_change():
    """Broadcast lock state change to all clients."""
    await broadcast({
        "type": "lock_change",
        "data": app_state.controller_lock.to_dict(),
    })


async def status_update_loop():
    """Background task to periodically broadcast status."""
    while True:
        try:
            tier = app_state.tier

            if tier == ActivationTier.HOT and ble_manager.connected:
                # Check if using notify mode (v1-p2) or polling mode (v1-p1)
                profile = get_profile(ble_manager.profile_id)
                if profile.get("status_mode") == "notify":
                    # v1-p2: Status comes via notify, just broadcast cached
                    await broadcast_status()
                    await asyncio.sleep(0.1)  # 100ms for notify mode
                else:
                    # v1-p1: Polling mode - read status from device
                    await ble_manager.read_status()
                    await broadcast_status()
                    await asyncio.sleep(0.5)  # 500ms for polling mode

            elif tier == ActivationTier.WARM:
                # Warm: Just broadcast cached status
                await broadcast_status()
                await asyncio.sleep(2.0)  # 2s for warm state

            else:
                # Always-on: Minimal activity
                await asyncio.sleep(5.0)

        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(1.0)


def start_status_task():
    """Start the background status update task."""
    global _status_task
    if _status_task is None or _status_task.done():
        _status_task = asyncio.create_task(status_update_loop())


def stop_status_task():
    """Stop the background status update task."""
    global _status_task
    if _status_task and not _status_task.done():
        _status_task.cancel()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection handler."""
    await websocket.accept()

    # Generate client ID and register
    client_id = app_state.generate_client_id()
    clients[client_id] = websocket
    app_state.add_client(client_id)

    # Start status task if needed
    start_status_task()

    # Setup BLE callbacks
    def on_log_event(message: str):
        asyncio.create_task(broadcast_log("INFO", message))

    def on_disconnect_callback():
        asyncio.create_task(broadcast_log("WARNING", "BLE device disconnected"))
        app_state.on_ble_disconnect()
        asyncio.create_task(broadcast_status())

    def on_status_update(status):
        # Broadcast status immediately when notify data arrives
        asyncio.create_task(broadcast_status())

    ble_manager.on_log_event = on_log_event
    ble_manager.on_disconnect = on_disconnect_callback
    ble_manager.on_status_update = on_status_update

    try:
        # Send initial state with cached device list
        await send_to_client(client_id, {
            "type": "init",
            "data": {
                "client_id": client_id,
                "app_state": app_state.get_state_info(),
                "devices": app_state.scanned_devices,
            },
        })
        await broadcast_status()

        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                await handle_ws_message(client_id, msg)
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        pass
    finally:
        # Cleanup
        clients.pop(client_id, None)
        app_state.remove_client(client_id)

        # Broadcast lock change if this client held it
        await broadcast_lock_change()

        # Stop task if no clients
        if not clients:
            stop_status_task()


async def handle_ws_message(client_id: str, msg: dict):
    """Handle incoming WebSocket message."""
    msg_type = msg.get("type")
    data = msg.get("data", {})

    # --- Control commands ---
    if msg_type == "command":
        action = data.get("action", "").lower()
        success = False

        if action in ("up", "open"):
            success = await ble_manager.send_up()
            await broadcast_log("INFO", f"Command sent: UP")
        elif action in ("down", "close"):
            success = await ble_manager.send_down()
            await broadcast_log("INFO", f"Command sent: DOWN")
        elif action == "stop":
            success = await ble_manager.send_stop()
            await broadcast_log("INFO", f"Command sent: STOP")
        else:
            await send_to_client(client_id, {
                "type": "error",
                "data": {"message": f"Unknown action: {action}"},
            })
            return

        await send_to_client(client_id, {
            "type": "command_result",
            "data": {"action": action, "success": success},
        })

    # --- Scan (no lock required) ---
    elif msg_type == "scan":
        from datetime import datetime
        from rvt_monitor.ble.scanner import scan_devices
        await broadcast_log("INFO", "Starting BLE scan...")
        devices = await scan_devices()
        # Cache results
        app_state.scanned_devices = [d.to_dict() for d in devices]
        app_state.last_scan_time = datetime.now()
        await broadcast({
            "type": "scan_result",
            "data": app_state.scanned_devices,
        })
        await broadcast_log("INFO", f"Scan complete: {len(devices)} devices found")

    # --- Connect ---
    elif msg_type == "connect":
        address = data.get("address")
        name = data.get("name", "")

        if not address:
            await send_to_client(client_id, {
                "type": "error",
                "data": {"message": "Address required"},
            })
            return

        await broadcast_log("INFO", f"Connecting to {name or address}...")
        try:
            success = await ble_manager.connect(address, name)
            if success:
                app_state.on_ble_connect()
                await broadcast_log("INFO", f"Connected to {name or address}")

                # Subscribe to status notifications for v1-p2 (notify mode)
                profile = get_profile(ble_manager.profile_id)
                if profile.get("status_mode") == "notify":
                    sub_ok = await ble_manager.subscribe_status()
                    if sub_ok:
                        await broadcast_log("INFO", "Subscribed to status notifications")
                    else:
                        await broadcast_log("WARNING", "Failed to subscribe to status")
            else:
                await broadcast_log("ERROR", f"Connection failed")
        except Exception as e:
            await broadcast_log("ERROR", f"Connection error: {e}")
            success = False

        await broadcast_status()

    # --- Disconnect ---
    elif msg_type == "disconnect":
        await ble_manager.disconnect()
        app_state.on_ble_disconnect()
        await broadcast_log("INFO", "Disconnected")
        await broadcast_status()

    # --- Lock control ---
    elif msg_type == "acquire_lock":
        name = data.get("name", "Unknown")
        success = app_state.acquire_control(client_id, name)
        await send_to_client(client_id, {
            "type": "lock_result",
            "data": {
                "action": "acquire",
                "success": success,
                "lock": app_state.controller_lock.to_dict(),
            },
        })
        if success:
            await broadcast_lock_change()
            await broadcast_log("INFO", f"{name} acquired control")

    elif msg_type == "release_lock":
        success = app_state.release_control(client_id)
        await send_to_client(client_id, {
            "type": "lock_result",
            "data": {
                "action": "release",
                "success": success,
                "lock": app_state.controller_lock.to_dict(),
            },
        })
        if success:
            await broadcast_lock_change()
            await broadcast_log("INFO", "Control released")

    # --- Set client name ---
    elif msg_type == "set_name":
        name = data.get("name", "Unknown")
        if client_id in app_state.clients:
            app_state.clients[client_id].name = name
        await send_to_client(client_id, {
            "type": "name_set",
            "data": {"name": name},
        })

    # --- Dimension operations ---
    elif msg_type == "read_dimensions":
        await broadcast_log("INFO", "Reading dimensions...")
        result = await ble_manager.read_all_dimensions()
        await send_to_client(client_id, {
            "type": "dimensions",
            "data": result,
        })
        if result:
            await broadcast_log("INFO", "Dimensions read successfully")
        else:
            await broadcast_log("ERROR", "Failed to read dimensions")

    elif msg_type == "write_dimension":
        dim_id = data.get("id")
        value = data.get("value")
        if dim_id is not None and value is not None:
            success = await ble_manager.write_dimension(dim_id, value)
            await send_to_client(client_id, {
                "type": "dimension_write_result",
                "data": {"id": dim_id, "value": value, "success": success},
            })
            if success:
                await broadcast_log("INFO", f"Dimension {dim_id} set to {value}")
            else:
                await broadcast_log("ERROR", f"Failed to write dimension {dim_id}")

    elif msg_type == "save_dimensions":
        await broadcast_log("INFO", "Saving dimensions to flash...")
        success = await ble_manager.save_dimensions()
        await send_to_client(client_id, {
            "type": "dimensions_save_result",
            "data": {"success": success},
        })
        if success:
            await broadcast_log("INFO", "Dimensions saved successfully")
        else:
            await broadcast_log("ERROR", "Failed to save dimensions")

    # --- WiFi provisioning ---
    elif msg_type == "read_wifi_status":
        result = await ble_manager.read_wifi_status()
        await send_to_client(client_id, {
            "type": "wifi_status",
            "data": result,
        })

    elif msg_type == "set_wifi":
        ssid = data.get("ssid", "")
        password = data.get("password", "")
        if ssid:
            await broadcast_log("INFO", f"Setting WiFi: {ssid}")
            success = await ble_manager.set_wifi_config(ssid, password)
            await send_to_client(client_id, {
                "type": "wifi_set_result",
                "data": {"ssid": ssid, "success": success},
            })
            if success:
                await broadcast_log("INFO", f"WiFi credentials set for {ssid}")
            else:
                await broadcast_log("ERROR", "Failed to set WiFi credentials")
        else:
            await send_to_client(client_id, {
                "type": "error",
                "data": {"message": "SSID required"},
            })
