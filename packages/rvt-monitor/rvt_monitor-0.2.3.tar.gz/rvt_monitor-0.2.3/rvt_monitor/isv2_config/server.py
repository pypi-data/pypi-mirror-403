"""ISV2 Config Web Server."""

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .protocol import ISV2Client, ISV2Error

# Global state
client: Optional[ISV2Client] = None
connected_websockets: set[WebSocket] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan handler."""
    yield
    # Cleanup on shutdown
    global client
    if client:
        client.close()
        client = None


app = FastAPI(title="ISV2 Config", version="0.1.0", lifespan=lifespan)

# Static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


def list_serial_ports() -> list[dict]:
    """List available serial ports (filtered to ttyUSB* and COM*)."""
    import serial.tools.list_ports
    ports = []
    for port in serial.tools.list_ports.comports():
        # Filter: only /dev/ttyUSB* (Linux) and COM* (Windows)
        if port.device.startswith("/dev/ttyUSB") or port.device.startswith("COM"):
            ports.append({
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid,
            })
    return ports


async def broadcast(message: dict):
    """Broadcast message to all connected WebSocket clients."""
    dead = set()
    for ws in connected_websockets:
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    connected_websockets.difference_update(dead)


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve main page."""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>ISV2 Config</h1><p>Static files not found</p>")


@app.get("/api/ports")
async def get_ports():
    """Get available serial ports."""
    return {"ports": list_serial_ports()}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()
    connected_websockets.add(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(websocket, data)
    except WebSocketDisconnect:
        pass
    finally:
        connected_websockets.discard(websocket)


async def handle_message(ws: WebSocket, data: dict):
    """Handle WebSocket message."""
    global client

    msg_type = data.get("type")

    try:
        if msg_type == "connect":
            port = data.get("port")
            baudrate = data.get("baudrate", 38400)
            address = data.get("address", 0x11)

            if client:
                client.close()

            client = ISV2Client(
                port=port,
                device_addr=address,
                baudrate=baudrate,
                verbose=False,
            )

            if client.open():
                await ws.send_json({
                    "type": "connected",
                    "port": port,
                    "baudrate": baudrate,
                    "address": f"0x{address:02X}",
                })
            else:
                client = None
                await ws.send_json({
                    "type": "error",
                    "message": f"Failed to open {port}",
                })

        elif msg_type == "disconnect":
            if client:
                client.close()
                client = None
            await ws.send_json({"type": "disconnected"})

        elif msg_type == "read":
            if not client:
                await ws.send_json({"type": "error", "message": "Not connected"})
                return

            address = int(data.get("address", "0"), 0)
            count = data.get("count", 1)

            # Enable verbose for debugging
            old_verbose = client.verbose
            client.verbose = True
            try:
                values = client.read(address, count)
                await ws.send_json({
                    "type": "read_result",
                    "address": f"0x{address:04X}",
                    "values": [f"0x{v:04X}" for v in values],
                    "decimal": values,
                })
            finally:
                client.verbose = old_verbose

        elif msg_type == "write":
            if not client:
                await ws.send_json({"type": "error", "message": "Not connected"})
                return

            address = int(data.get("address", "0"), 0)
            value = int(data.get("value", "0"), 0)
            bits = data.get("bits", 16)

            if bits == 32:
                success = client.write32(address, value)
            else:
                success = client.write16(address, value)

            await ws.send_json({
                "type": "write_result",
                "address": f"0x{address:04X}",
                "value": f"0x{value:04X}" if bits == 16 else f"0x{value:08X}",
                "success": success,
            })

        elif msg_type == "save":
            if not client:
                await ws.send_json({"type": "error", "message": "Not connected"})
                return

            success = client.save()
            await ws.send_json({
                "type": "save_result",
                "success": success,
            })

        elif msg_type == "status":
            if not client:
                await ws.send_json({"type": "error", "message": "Not connected"})
                return

            status = client.read_status()
            await ws.send_json({
                "type": "status_result",
                "enabled": status["enabled"],
                "ready": status["ready"],
                "alarm": status["alarm"],
                "status_raw": f"0x{status['status_raw']:04X}",
            })

        elif msg_type == "list_ports":
            ports = list_serial_ports()
            await ws.send_json({
                "type": "ports_list",
                "ports": ports,
            })

        elif msg_type == "check_connection":
            if client and client._serial.is_open():
                await ws.send_json({
                    "type": "connected",
                    "port": client._serial.port,
                    "baudrate": client._serial.baudrate,
                    "address": f"0x{client.device_addr:02X}",
                })
            else:
                await ws.send_json({"type": "disconnected"})

        elif msg_type == "read_baudrate":
            if not client:
                await ws.send_json({"type": "error", "message": "Not connected"})
                return

            result = client.read_baudrate()
            await ws.send_json({
                "type": "baudrate_result",
                "value": result["value"],
                "baudrate": result["baudrate"],
            })

        elif msg_type == "set_baudrate":
            if not client:
                await ws.send_json({"type": "error", "message": "Not connected"})
                return

            value = data.get("value", 2)  # Default to 38400
            success = client.set_baudrate(value)
            await ws.send_json({
                "type": "set_baudrate_result",
                "success": success,
                "value": value,
                "baudrate": client.BAUD_RATES.get(value),
            })

        elif msg_type == "factory_reset":
            if not client:
                await ws.send_json({"type": "error", "message": "Not connected"})
                return

            # Check enable status first
            if client.is_enabled():
                await ws.send_json({
                    "type": "error",
                    "message": "Motor is enabled. Disable motor first.",
                })
                return

            success = client.factory_reset(force=True)
            await ws.send_json({
                "type": "factory_reset_result",
                "success": success,
            })

        elif msg_type == "run_motor_setting":
            if not client:
                await ws.send_json({"type": "error", "message": "Not connected"})
                return

            target_baudrate = data.get("baudrate", 4)  # Default 38400

            try:
                # Step 1: Check status
                await ws.send_json({"type": "sequence_progress", "step": 1, "message": "Reading motor status..."})
                await asyncio.sleep(0.1)
                enabled = client.is_enabled()
                if enabled:
                    await ws.send_json({
                        "type": "sequence_error",
                        "step": 1,
                        "message": "Motor is enabled. Disable motor first.",
                    })
                    return
                await ws.send_json({"type": "sequence_progress", "step": 1, "message": "Motor is disabled. OK"})
                await asyncio.sleep(0.1)

                # Step 2: Factory reset
                await ws.send_json({"type": "sequence_progress", "step": 2, "message": "Factory reset..."})
                await asyncio.sleep(0.1)
                client.factory_reset(force=True)
                await ws.send_json({"type": "sequence_progress", "step": 2, "message": "Factory reset done"})
                await asyncio.sleep(0.1)

                # Step 3: Set baud rate
                await ws.send_json({"type": "sequence_progress", "step": 3, "message": f"Setting baud rate to {target_baudrate}..."})
                await asyncio.sleep(0.1)
                client.set_baudrate(target_baudrate)
                await ws.send_json({"type": "sequence_progress", "step": 3, "message": "Baud rate set"})
                await asyncio.sleep(0.1)

                # Step 4: Save to motor
                await ws.send_json({"type": "sequence_progress", "step": 4, "message": "Saving to motor..."})
                await asyncio.sleep(0.1)
                client.save()
                await ws.send_json({"type": "sequence_progress", "step": 4, "message": "Saved"})
                await asyncio.sleep(0.1)

                # Step 5: Read parameters
                await ws.send_json({"type": "sequence_progress", "step": 5, "message": "Reading parameters..."})
                await asyncio.sleep(0.1)
                params = client.read_all_params()

                # Step 6: Read motor status
                await ws.send_json({"type": "sequence_progress", "step": 6, "message": "Reading motor status..."})
                await asyncio.sleep(0.1)
                status = client.read_status()

                await ws.send_json({
                    "type": "sequence_complete",
                    "message": "Motor setting completed!",
                    "params": params,
                    "status": {
                        "enabled": status["enabled"],
                        "ready": status["ready"],
                        "alarm": status["alarm"],
                    },
                })

            except Exception as e:
                await ws.send_json({"type": "sequence_error", "step": 0, "message": str(e)})

        elif msg_type == "read_params":
            if not client:
                await ws.send_json({"type": "error", "message": "Not connected"})
                return

            results = client.read_all_params()
            await ws.send_json({
                "type": "params_result",
                "params": results,
            })

        elif msg_type == "set_param":
            if not client:
                await ws.send_json({"type": "error", "message": "Not connected"})
                return

            param_name = data.get("name")
            value = int(data.get("value", 0))

            success = client.write_param(param_name, value)
            await ws.send_json({
                "type": "set_param_result",
                "success": success,
                "name": param_name,
                "value": value,
            })

    except ISV2Error as e:
        await ws.send_json({
            "type": "error",
            "message": str(e),
        })
    except Exception as e:
        await ws.send_json({
            "type": "error",
            "message": f"Unexpected error: {e}",
        })


def run_server(host: str = "127.0.0.1", port: int = 8001):
    """Run the web server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
