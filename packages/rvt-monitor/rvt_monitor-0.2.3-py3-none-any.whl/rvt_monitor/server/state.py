"""Global application state with 3-tier activation model."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Set
import uuid


class ActivationTier(Enum):
    """Server activation tier."""
    ALWAYS_ON = "always_on"  # Server running, minimal activity
    WARM = "warm"           # WebSocket connected, status polling
    HOT = "hot"             # BLE connected, full functionality


@dataclass
class ControllerLock:
    """Controller lock for single-writer access."""
    holder_id: Optional[str] = None
    holder_name: Optional[str] = None
    acquired_at: Optional[datetime] = None

    def is_locked(self) -> bool:
        return self.holder_id is not None

    def is_held_by(self, client_id: str) -> bool:
        return self.holder_id == client_id

    def acquire(self, client_id: str, name: str = "Unknown") -> bool:
        """Try to acquire the lock."""
        if self.holder_id is None:
            self.holder_id = client_id
            self.holder_name = name
            self.acquired_at = datetime.now()
            return True
        return self.holder_id == client_id  # Already held by this client

    def release(self, client_id: str) -> bool:
        """Release the lock if held by this client."""
        if self.holder_id == client_id:
            self.holder_id = None
            self.holder_name = None
            self.acquired_at = None
            return True
        return False

    def force_release(self):
        """Force release the lock (admin action)."""
        self.holder_id = None
        self.holder_name = None
        self.acquired_at = None

    def to_dict(self) -> dict:
        return {
            "locked": self.is_locked(),
            "holder_id": self.holder_id,
            "holder_name": self.holder_name,
            "acquired_at": self.acquired_at.isoformat() if self.acquired_at else None,
        }


@dataclass
class ClientInfo:
    """Information about a connected WebSocket client."""
    client_id: str
    name: str = "Unknown"
    connected_at: datetime = field(default_factory=datetime.now)
    is_viewer: bool = True  # True = viewer only, False = has control


class AppState:
    """
    Global application state manager.

    Activation Tiers:
    - ALWAYS_ON: Server is running but no clients connected
    - WARM: At least one WebSocket client connected
    - HOT: BLE device is connected

    Controller Lock:
    - Only one client can hold the controller lock at a time
    - Lock holder can send commands (UP/DOWN/STOP, LED, config)
    - Viewers can see status but cannot control
    """

    def __init__(self):
        from rvt_monitor.ble.manager import BLEManager

        self.ble_manager = BLEManager()
        self.controller_lock = ControllerLock()
        self.clients: dict[str, ClientInfo] = {}
        self._tier = ActivationTier.ALWAYS_ON
        self._status_task: Optional[asyncio.Task] = None
        # Cached scan results
        self.scanned_devices: list = []
        self.last_scan_time: Optional[datetime] = None

    @property
    def tier(self) -> ActivationTier:
        return self._tier

    @property
    def client_count(self) -> int:
        return len(self.clients)

    def generate_client_id(self) -> str:
        """Generate a unique client ID."""
        return str(uuid.uuid4())[:8]

    def add_client(self, client_id: str, name: str = "Unknown") -> ClientInfo:
        """Register a new WebSocket client."""
        info = ClientInfo(client_id=client_id, name=name)
        self.clients[client_id] = info
        self._update_tier()
        return info

    def remove_client(self, client_id: str):
        """Unregister a WebSocket client."""
        if client_id in self.clients:
            del self.clients[client_id]

        # Release lock if held by this client
        self.controller_lock.release(client_id)
        self._update_tier()

    def _update_tier(self):
        """Update activation tier based on current state."""
        if self.ble_manager.connected:
            self._tier = ActivationTier.HOT
        elif self.client_count > 0:
            self._tier = ActivationTier.WARM
        else:
            self._tier = ActivationTier.ALWAYS_ON

    def on_ble_connect(self):
        """Called when BLE device connects."""
        self._tier = ActivationTier.HOT

    def on_ble_disconnect(self):
        """Called when BLE device disconnects."""
        self._update_tier()

    def can_control(self, client_id: str) -> bool:
        """Check if client can send control commands."""
        return self.controller_lock.is_held_by(client_id)

    def acquire_control(self, client_id: str, name: str = "Unknown") -> bool:
        """Try to acquire controller lock."""
        if self.controller_lock.acquire(client_id, name):
            if client_id in self.clients:
                self.clients[client_id].is_viewer = False
            return True
        return False

    def release_control(self, client_id: str) -> bool:
        """Release controller lock."""
        if self.controller_lock.release(client_id):
            if client_id in self.clients:
                self.clients[client_id].is_viewer = True
            return True
        return False

    def get_state_info(self) -> dict:
        """Get current application state."""
        return {
            "tier": self._tier.value,
            "client_count": self.client_count,
            "lock": self.controller_lock.to_dict(),
            "ble_connected": self.ble_manager.connected,
        }


# Global state instance
app_state = AppState()

# Convenience alias
ble_manager = app_state.ble_manager
