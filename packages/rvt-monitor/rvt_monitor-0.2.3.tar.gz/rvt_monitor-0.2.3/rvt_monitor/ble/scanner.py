"""BLE Device Scanner."""

import logging
from dataclasses import dataclass
from typing import Optional

from bleak import BleakScanner

from .protocol import DEVICE_PREFIX_CEILY, DEVICE_PREFIX_WALLY

logger = logging.getLogger(__name__)


@dataclass
class ScannedDevice:
    """Scanned BLE device info."""
    name: str
    address: str
    rssi: int
    device_type: Optional[str] = None  # "ceily" or "wally"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "address": self.address,
            "rssi": self.rssi,
            "device_type": self.device_type,
        }


def detect_device_type(name: str) -> Optional[str]:
    """Detect device type from name prefix."""
    if name.startswith(DEVICE_PREFIX_CEILY):
        return "ceily"
    elif name.startswith(DEVICE_PREFIX_WALLY):
        return "wally"
    return None


async def scan_devices(
    timeout: float = 5.0,
    prefix: str = "",
    show_all: bool = False,
) -> list[ScannedDevice]:
    """
    Scan for BLE devices.

    Args:
        timeout: Scan timeout in seconds
        prefix: Filter devices by name prefix (empty = all RVT devices)
        show_all: If True, show all BLE devices (for debugging)

    Returns:
        List of ScannedDevice objects
    """
    logger.info(f"Starting BLE scan (timeout={timeout}s, show_all={show_all})")

    # Use discover with return_adv=True to get RSSI
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)

    logger.info(f"Raw scan found {len(devices)} devices")

    results: list[ScannedDevice] = []

    for address, (device, adv_data) in devices.items():
        name = device.name or adv_data.local_name or ""
        rssi = adv_data.rssi if adv_data.rssi else -100

        # Debug: log all discovered devices
        logger.debug(f"  Found: {name!r} ({address}) RSSI={rssi}")

        if not name:
            continue

        # Filter by prefix if specified
        if prefix and not name.startswith(prefix):
            continue

        # Detect device type
        device_type = detect_device_type(name)

        # Filter to only RVT devices (Ceily/Wally) if no prefix specified
        # Unless show_all is True
        if not show_all and not prefix and device_type is None:
            continue

        results.append(ScannedDevice(
            name=name,
            address=address,
            rssi=rssi,
            device_type=device_type,
        ))

    # Sort by RSSI (strongest first)
    results.sort(key=lambda d: d.rssi, reverse=True)

    logger.info(f"Filtered results: {len(results)} devices")

    return results
