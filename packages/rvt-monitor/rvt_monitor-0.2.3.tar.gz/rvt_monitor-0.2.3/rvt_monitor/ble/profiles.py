"""Profile definitions for BLE device version detection.

Profiles are determined by the presence of Device Info Service (0x180A):
- v1-p1: Legacy firmware without Device Info Service
- v1-p2: Current firmware with Device Info Service
"""

from typing import List
from uuid import UUID

# BLE SIG Device Information Service UUID
DEVICE_INFO_SERVICE_UUID = UUID("0000180a-0000-1000-8000-00805f9b34fb")

PROFILES = {
    "v1-p1": {
        "has_device_info": False,
        "status_mode": "polling",  # Use read polling for status
        "description": "Legacy firmware without Device Info Service",
    },
    "v1-p2": {
        "has_device_info": True,
        "status_mode": "notify",  # Use BLE notify for status
        "description": "Firmware with Device Info Service",
    },
}


def detect_profile(service_uuids: List[UUID]) -> str:
    """Detect profile from discovered BLE services.

    Args:
        service_uuids: List of service UUIDs from the connected device.

    Returns:
        Profile ID string ("v1-p1" or "v1-p2").
    """
    # Normalize UUIDs for comparison (handle both str and UUID)
    normalized = []
    for uuid in service_uuids:
        if isinstance(uuid, str):
            normalized.append(UUID(uuid))
        else:
            normalized.append(uuid)

    if DEVICE_INFO_SERVICE_UUID in normalized:
        return "v1-p2"
    return "v1-p1"


def get_profile(profile_id: str) -> dict:
    """Get profile configuration by ID.

    Args:
        profile_id: Profile ID string.

    Returns:
        Profile configuration dict. Falls back to v1-p2 if not found.
    """
    return PROFILES.get(profile_id, PROFILES["v1-p2"])
