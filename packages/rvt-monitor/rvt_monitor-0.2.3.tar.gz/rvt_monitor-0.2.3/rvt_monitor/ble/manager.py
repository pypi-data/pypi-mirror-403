"""BLE Connection Manager."""

import asyncio
import struct
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, Union

from bleak import BleakClient
from bleak.exc import BleakError

from .protocol import (
    CharUUID,
    ServiceUUID,
    MotionCommand,
    MotionState,
    build_motion_command,
    build_led_brightness,
    build_led_color_index,
    build_torque_command,
    build_dimension_write,
    build_wifi_config,
    TorqueCommand,
    DimensionCommand,
    LEDTarget,
)
from .scanner import detect_device_type
from .profiles import detect_profile, get_profile


class ConnectionState(Enum):
    """BLE connection state."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"


@dataclass
class TofStatus:
    """ToF sensor status.

    v1-p1: status byte = (state << 4) | error_code
    v1-p2: status byte = enable(1) | state(2) | rsv(1) | error(3) | rsv(1)
    """
    enable: bool = True
    state: int = 0       # 0=Init, 1=Run, 2=Disconnected
    error_code: int = 0  # 0=None, 1=InitFailed, 2=Disconnected, 3=InvalidData, 4=DataNotReady
    object_detected: bool = False

    STATE_NAMES = {0: "Init", 1: "Run", 2: "Disconnected"}
    ERROR_NAMES = {0: "None", 1: "InitFailed", 2: "Disconnected", 3: "InvalidData", 4: "DataNotReady"}

    @classmethod
    def from_bytes_v1(cls, status_byte: int, object_detected: bool) -> "TofStatus":
        """Parse v1-p1 format: high nibble = state, low nibble = error."""
        return cls(
            enable=True,  # v1-p1 has no enable field
            state=(status_byte >> 4) & 0x0F,
            error_code=status_byte & 0x0F,
            object_detected=object_detected,
        )

    @classmethod
    def from_bytes_v2(cls, status_byte: int, data_byte: int) -> "TofStatus":
        """Parse v1-p2 format: new bit layout."""
        return cls(
            enable=bool(status_byte & 0x01),
            state=(status_byte >> 1) & 0x03,
            error_code=(status_byte >> 4) & 0x07,
            object_detected=bool(data_byte),
        )

    def to_dict(self) -> dict:
        return {
            "enable": self.enable,
            "state": self.state,
            "state_name": self.STATE_NAMES.get(self.state, f"Unknown({self.state})"),
            "error_code": self.error_code,
            "error_name": self.ERROR_NAMES.get(self.error_code, f"Unknown({self.error_code})"),
            "object_detected": self.object_detected,
        }


@dataclass
class CeilyStatus:
    """Ceily device status (66 bytes)."""
    motion_state: MotionState = MotionState.INIT
    mcu_temp: int = 0  # MCU temperature in Celsius
    # Common fields (v1-p2)
    speed_control_state: int = 0
    position_percentage: int = 0
    position_mm: int = 0
    remain_distance: int = 0
    torque: int = 0
    current_velocity: int = 0
    command_velocity: int = 0
    is_position_verified: bool = False
    is_current_model_learning: bool = False
    motion_phase: int = 0
    # ToF sensors
    tof_front: TofStatus = field(default_factory=TofStatus)
    tof_left: TofStatus = field(default_factory=TofStatus)
    tof_right: TofStatus = field(default_factory=TofStatus)
    # Limit switches (bit 0: bottom, bit 1: top)
    limit_switch_state: int = 0
    top_limit: bool = False
    bottom_limit: bool = False
    # Servo
    servo_connected: bool = False
    servo_enabled: bool = False
    servo_current_alarm: int = 0
    # v1-p1: position, velocity_mm, torque (float)
    servo_position: int = 0
    velocity_mm: float = 0.0
    raw_velocity: int = 0
    raw_torque: int = 0
    # Motor status
    motor_current: int = 0
    voltage: int = 0
    temperature: int = 0
    last_update: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "device_type": "ceily",
            "motion_state": self.motion_state.name,
            "mcu_temp": self.mcu_temp,
            "speed_control_state": self.speed_control_state,
            "position_percentage": self.position_percentage,
            "position_mm": self.position_mm,
            "remain_distance": self.remain_distance,
            "torque": self.torque,
            "current_velocity": self.current_velocity,
            "command_velocity": self.command_velocity,
            "is_position_verified": self.is_position_verified,
            "is_current_model_learning": self.is_current_model_learning,
            "motion_phase": self.motion_phase,
            "tof_front": self.tof_front.to_dict(),
            "tof_left": self.tof_left.to_dict(),
            "tof_right": self.tof_right.to_dict(),
            "limit_switch_state": self.limit_switch_state,
            "top_limit": self.top_limit,
            "bottom_limit": self.bottom_limit,
            "servo_connected": self.servo_connected,
            "servo_enabled": self.servo_enabled,
            "servo_current_alarm": self.servo_current_alarm,
            "servo_position": self.servo_position,
            "velocity_mm": self.velocity_mm,
            "raw_velocity": self.raw_velocity,
            "raw_torque": self.raw_torque,
            "motor_current": self.motor_current,
            "voltage": self.voltage,
            "temperature": self.temperature,
            "last_update": self.last_update.isoformat(),
        }


@dataclass
class WallyMotorStatus:
    """Single motor status for Wally.

    v1-p2: position (raw), position_mm, velocity, torque (floats)
    v1-p3: is_connected, raw_velocity, raw_torque (int16)
    """
    is_connected: bool = False
    is_enabled: bool = False
    current_alarm: int = 0
    # v1-p2 fields
    position: int = 0
    position_mm: float = 0.0
    velocity: float = 0.0
    torque: float = 0.0
    # v1-p3 fields
    raw_velocity: int = 0
    raw_torque: int = 0
    # Common fields
    current: int = 0
    voltage: int = 0
    temperature: int = 0

    def to_dict(self) -> dict:
        return {
            "is_connected": self.is_connected,
            "is_enabled": self.is_enabled,
            "current_alarm": self.current_alarm,
            "position": self.position,
            "position_mm": self.position_mm,
            "velocity": self.velocity,
            "torque": self.torque,
            "raw_velocity": self.raw_velocity,
            "raw_torque": self.raw_torque,
            "current": self.current,
            "voltage": self.voltage,
            "temperature": self.temperature,
        }


@dataclass
class WallyTofStatus:
    """Wally ToF sensor status with distance.

    v1-p1: status(1) + distance(4B float mm)
    v1-p2: status(1) + distance(1B uint8 cm)
    """
    enable: bool = True
    state: int = 0
    error_code: int = 0
    distance_mm: float = 0.0  # For compatibility, store in mm

    STATE_NAMES = {0: "Init", 1: "Run", 2: "Disconnected"}
    ERROR_NAMES = {0: "None", 1: "InitFailed", 2: "Disconnected", 3: "InvalidData", 4: "DataNotReady"}

    @classmethod
    def from_bytes_v1(cls, status_byte: int, distance_mm: float) -> "WallyTofStatus":
        """Parse v1-p1 format: old status byte + float distance."""
        return cls(
            enable=True,
            state=(status_byte >> 4) & 0x0F,
            error_code=status_byte & 0x0F,
            distance_mm=distance_mm,
        )

    @classmethod
    def from_bytes_v2(cls, status_byte: int, distance_cm: int) -> "WallyTofStatus":
        """Parse v1-p2 format: new status byte + uint8 cm."""
        return cls(
            enable=bool(status_byte & 0x01),
            state=(status_byte >> 1) & 0x03,
            error_code=(status_byte >> 4) & 0x07,
            distance_mm=float(distance_cm * 10),  # Convert cm to mm
        )

    def to_dict(self) -> dict:
        return {
            "enable": self.enable,
            "state": self.state,
            "state_name": self.STATE_NAMES.get(self.state, f"Unknown({self.state})"),
            "error_code": self.error_code,
            "error_name": self.ERROR_NAMES.get(self.error_code, f"Unknown({self.error_code})"),
            "distance_mm": self.distance_mm,
        }


@dataclass
class WallyStatus:
    """Wally device status (v1-p1: 106 bytes, v1-p2: 80 bytes)."""
    motion_state: MotionState = MotionState.INIT
    mcu_temp: int = 0  # MCU temperature in Celsius
    # Common fields (v1-p2)
    speed_control_state: int = 0
    position_percentage: int = 0
    position_mm: int = 0
    remain_distance: int = 0
    torque: int = 0
    current_velocity: int = 0
    command_velocity: int = 0
    is_position_verified: bool = False
    is_current_model_learning: bool = False
    motion_phase: int = 0
    # ToF sensors
    tof_left: WallyTofStatus = field(default_factory=WallyTofStatus)
    tof_right: WallyTofStatus = field(default_factory=WallyTofStatus)
    # Limit switch
    limit_switch_state: int = 0
    photo_sensor_state: int = 0
    # Motors
    motor_left: WallyMotorStatus = field(default_factory=WallyMotorStatus)
    motor_right: WallyMotorStatus = field(default_factory=WallyMotorStatus)
    # Wally kinematics (all floats from Vector2D)
    wally_x: float = 0.0
    wally_y: float = 0.0
    distance_to_wall: int = 0  # int16
    angle: float = 0.0
    # Control (v1-p1 only)
    target_x: float = 0.0
    target_y: float = 0.0
    target_velocity: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "device_type": "wally",
            "motion_state": self.motion_state.name,
            "mcu_temp": self.mcu_temp,
            "speed_control_state": self.speed_control_state,
            "position_percentage": self.position_percentage,
            "position_mm": self.position_mm,
            "remain_distance": self.remain_distance,
            "torque": self.torque,
            "current_velocity": self.current_velocity,
            "command_velocity": self.command_velocity,
            "is_position_verified": self.is_position_verified,
            "is_current_model_learning": self.is_current_model_learning,
            "motion_phase": self.motion_phase,
            "tof_left": self.tof_left.to_dict(),
            "tof_right": self.tof_right.to_dict(),
            "limit_switch_state": self.limit_switch_state,
            "photo_sensor_state": self.photo_sensor_state,
            "motor_left": self.motor_left.to_dict(),
            "motor_right": self.motor_right.to_dict(),
            "wally_x": self.wally_x,
            "wally_y": self.wally_y,
            "distance_to_wall": self.distance_to_wall,
            "angle": self.angle,
            "target_x": self.target_x,
            "target_y": self.target_y,
            "target_velocity": self.target_velocity,
            "last_update": self.last_update.isoformat(),
        }


DeviceStatus = Union[CeilyStatus, WallyStatus]


class BLEManager:
    """BLE connection and communication manager."""

    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.device_address: Optional[str] = None
        self.device_name: Optional[str] = None
        self.device_type: Optional[str] = None
        self.connection_state = ConnectionState.DISCONNECTED
        self.status: Optional[DeviceStatus] = None
        self.device_info: Optional[dict] = None  # BLE SIG Device Information
        self.profile_id: str = "v1-p2"  # Profile version (v1-p1 or v1-p2)
        self.rssi: int = -100
        self.last_packet_time: Optional[datetime] = None

        # Status subscription state (for v1-p2 notify mode)
        self._status_subscribed: bool = False

        # Callbacks
        self.on_state_change: Optional[Callable[[ConnectionState], None]] = None
        self.on_status_update: Optional[Callable[[DeviceStatus], None]] = None
        self.on_log_event: Optional[Callable[[str], None]] = None
        self.on_disconnect: Optional[Callable[[], None]] = None

        # Stats
        self.command_success_count = 0
        self.command_error_count = 0

    @property
    def connected(self) -> bool:
        return (
            self.connection_state == ConnectionState.CONNECTED
            and self.client is not None
            and self.client.is_connected
        )

    def _set_state(self, state: ConnectionState):
        """Update connection state and notify callback."""
        self.connection_state = state
        if self.on_state_change:
            self.on_state_change(state)

    def _on_disconnect(self, client: BleakClient):
        """Handle unexpected disconnection."""
        # Only handle disconnect if we were actually connected
        # Ignore spurious disconnect callbacks during connection attempts
        if self.connection_state != ConnectionState.CONNECTED:
            return
        self._set_state(ConnectionState.DISCONNECTED)
        self._status_subscribed = False
        self.client = None
        if self.on_disconnect:
            self.on_disconnect()

    def _handle_notification(self, sender, data: bytearray):
        """Handle BLE notification (log events).

        BleLogMessage structure (15 bytes):
        - uint32_t timestamp (4 bytes)
        - uint16_t protocol_version (2 bytes)
        - uint8_t event_type (1 byte)
        - uint8_t data[8] (8 bytes)

        Event types:
        - 3 = WiFi connection status changed
        """
        self.last_packet_time = datetime.now()
        try:
            if len(data) >= 15:
                # Parse binary log message
                timestamp = struct.unpack_from("<I", data, 0)[0]
                protocol_ver = struct.unpack_from("<H", data, 4)[0]
                event_type = data[6]
                event_data = data[7:15]

                message = self._format_log_event(event_type, event_data, timestamp)
                if message and self.on_log_event:
                    self.on_log_event(message)
            else:
                # Try as plain text (fallback)
                message = data.decode("utf-8", errors="replace").strip()
                if message and self.on_log_event:
                    self.on_log_event(message)
        except Exception:
            pass

    def _handle_status_notification(self, sender, data: bytearray):
        """Handle BLE status notification (v1-p2 notify mode)."""
        self.last_packet_time = datetime.now()
        try:
            if self.device_type == "ceily":
                self.status = self._parse_ceily_status(bytes(data))
            elif self.device_type == "wally":
                self.status = self._parse_wally_status(bytes(data))

            if self.on_status_update and self.status:
                self.on_status_update(self.status)
        except Exception:
            pass

    def _format_log_event(self, event_type: int, data: bytes, timestamp: int) -> str:
        """Format binary log event to human-readable string."""
        # Event type 0: None - ignore
        if event_type == 0:
            return None

        # Event type 1: Command received
        if event_type == 1:
            sender = data[0]
            command = data[1]
            cmd_names = {0: "Stop", 1: "Up", 2: "Down"}
            sender_names = {0: "None", 1: "Button", 2: "BLE", 3: "System"}
            cmd_str = cmd_names.get(command, f"Unknown({command})")
            sender_str = sender_names.get(sender, f"Unknown({sender})")
            return f"Command: {cmd_str} from {sender_str}"

        # Event type 2: Motion state changed
        if event_type == 2:
            state_from = data[0]
            state_to = data[1]
            position = data[2]
            error_code = data[3]
            state_names = {
                0: "Down", 1: "Up", 2: "Moving Down", 3: "Moving Up",
                4: "Stop", 5: "Emergency", 255: "Init"
            }
            error_names = {
                0: "None",
                1: "Not initialized",
                2: "Device error",
                3: "Collision detected",
                4: "Object detected",
                5: "E-stop activated",
                0x20: "Wally start env error",
                0x21: "Wally slip occurred",
                0x22: "Wally ToF angle error",
            }
            from_str = state_names.get(state_from, f"Unknown({state_from})")
            to_str = state_names.get(state_to, f"Unknown({state_to})")
            err_str = error_names.get(error_code, f"Unknown({error_code})")
            if error_code == 0:
                return f"State: {from_str} -> {to_str}, pos={position}"
            return f"State: {from_str} -> {to_str}, pos={position}, err={err_str}"

        # Event type 3: WiFi connection status
        if event_type == 3:
            status = data[0]
            rssi = struct.unpack("<b", data[1:2])[0]  # signed int8
            if status == 1:  # Connected
                channel = data[2]
                return f"WiFi Connected: ch={channel}, RSSI={rssi}dBm"
            elif status == 2:  # Disconnected
                reason = data[3]
                reason_text = {
                    1: "Unspecified", 2: "Auth expire", 3: "Auth leave",
                    4: "Assoc expire", 5: "Assoc toomany", 6: "Not authed",
                    7: "Not assoced", 8: "Assoc leave", 9: "Assoc not authed",
                    15: "4-way handshake timeout", 16: "Group key update timeout",
                    23: "802.1X auth failed", 200: "Beacon timeout",
                    201: "No AP found", 202: "Auth fail", 203: "Assoc fail",
                    204: "Handshake timeout",
                }.get(reason, f"Unknown({reason})")
                return f"WiFi Disconnected: reason={reason_text}, RSSI={rssi}dBm"
            else:
                return f"WiFi Status: {status}"

        # Unknown event type - show hex
        hex_data = data[:8].hex()
        return f"Event[{event_type}]: {hex_data}"

    async def connect(self, address: str, name: str = "") -> bool:
        """Connect to a BLE device."""
        if self.connected:
            await self.disconnect()

        self._set_state(ConnectionState.CONNECTING)
        self.device_address = address
        self.device_name = name
        self.device_type = detect_device_type(name) if name else None

        # Initialize status based on device type
        if self.device_type == "ceily":
            self.status = CeilyStatus()
        elif self.device_type == "wally":
            self.status = WallyStatus()
        else:
            self.status = None

        try:
            self.client = BleakClient(
                address,
                disconnected_callback=self._on_disconnect,
            )

            await asyncio.wait_for(
                self.client.connect(),
                timeout=20.0,
            )

            # Check if client was disconnected during connection attempt
            if self.client is None or not self.client.is_connected:
                raise BleakError("Connection failed")

            # Start notification for log events
            try:
                if self.client:
                    await self.client.start_notify(
                        CharUUID.LOG_EVENT,
                        self._handle_notification,
                    )
            except Exception:
                pass

            # Verify still connected after notification setup
            if self.client is None or not self.client.is_connected:
                raise BleakError("Connection lost during setup")

            self._set_state(ConnectionState.CONNECTED)
            self.last_packet_time = datetime.now()

            # Detect profile from available services
            services = self.client.services
            service_uuids = [str(s.uuid) for s in services]
            self.profile_id = detect_profile(service_uuids)
            print(f"[BLE] Detected profile: {self.profile_id}, services: {service_uuids}")

            # Read Device Information Service only for v1-p2
            if get_profile(self.profile_id)["has_device_info"]:
                self.device_info = await self.read_device_info()
            else:
                self.device_info = None

            return True

        except asyncio.TimeoutError:
            self._set_state(ConnectionState.DISCONNECTED)
            if self.client:
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
            self.client = None
            return False
        except BleakError:
            self._set_state(ConnectionState.DISCONNECTED)
            if self.client:
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
            self.client = None
            raise
        except Exception:
            self._set_state(ConnectionState.DISCONNECTED)
            if self.client:
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
            self.client = None
            return False

    async def disconnect(self):
        """Disconnect from current device."""
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass
            self.client = None
        self.device_info = None
        self._status_subscribed = False
        self._set_state(ConnectionState.DISCONNECTED)

    def _parse_ceily_status(self, data: bytes) -> CeilyStatus:
        """Parse Ceily system status (66 bytes)."""
        status = CeilyStatus()


        # Determine actual format based on data length
        # v1-p2: 37+ bytes, v1-p1: 33 bytes (or shorter for older firmware)
        use_v2_format = self.profile_id == "v1-p2" and len(data) >= 37

        # Update profile_id if format doesn't match (for frontend UI)
        if self.profile_id == "v1-p2" and not use_v2_format:
            print(f"[BLE] Ceily: Data format mismatch, switching to v1-p1 UI")
            self.profile_id = "v1-p1"

        if use_v2_format:
            # Common (17 bytes)
            status.motion_state = MotionState(data[0])
            status.mcu_temp = struct.unpack("<b", data[1:2])[0]  # int8
            status.speed_control_state = data[2]
            status.position_percentage = data[3]
            status.position_mm = struct.unpack("<h", data[4:6])[0]  # signed int16
            status.remain_distance = struct.unpack("<h", data[6:8])[0]  # signed int16
            status.torque = struct.unpack("<h", data[8:10])[0]  # signed int16
            status.current_velocity = struct.unpack("<h", data[10:12])[0]  # signed int16
            status.command_velocity = struct.unpack("<h", data[12:14])[0]  # signed int16
            status.is_position_verified = bool(data[14])
            status.is_current_model_learning = bool(data[15])
            status.motion_phase = data[16]
            # Sensors (7 bytes, offset 17)
            status.tof_front = TofStatus.from_bytes_v2(data[17], data[18])
            status.tof_left = TofStatus.from_bytes_v2(data[19], data[20])
            status.tof_right = TofStatus.from_bytes_v2(data[21], data[22])
            # Limit switch: bit 0 = bottom, bit 1 = top
            status.limit_switch_state = data[23]
            status.bottom_limit = bool(data[23] & 0x01)
            status.top_limit = bool(data[23] & 0x02)
            # Motor (13 bytes, offset 24)
            # bit 0: is_connected, bit 1: is_enabled
            motor_status_byte = data[24]
            status.servo_connected = bool(motor_status_byte & 0x01)
            status.servo_enabled = bool(motor_status_byte & 0x02)
            status.servo_current_alarm = struct.unpack("<H", data[25:27])[0]
            status.raw_velocity = struct.unpack("<h", data[27:29])[0]
            status.raw_torque = struct.unpack("<h", data[29:31])[0]
            status.motor_current = struct.unpack("<h", data[31:33])[0]
            status.voltage = struct.unpack("<h", data[33:35])[0]
            status.temperature = struct.unpack("<h", data[35:37])[0]
        else:
            # v1-p1: old format with float kinematics
            # Layout: motion(1) + tof(6) + limit(1) + servo_conn(1) + alarm(2) + servo_pos(4)
            #         + position_mm(4f) + velocity_mm(4f) + torque(4f) + current(2) + voltage(2) + temp(2)
            # Total: 33 bytes
            if len(data) < 33:
                return status
            status.motion_state = MotionState(data[0])
            status.tof_front = TofStatus.from_bytes_v1(data[1], bool(data[2]))
            status.tof_left = TofStatus.from_bytes_v1(data[3], bool(data[4]))
            status.tof_right = TofStatus.from_bytes_v1(data[5], bool(data[6]))
            # Limit switch: bit 0 = bottom, bit 1 = top
            status.limit_switch_state = data[7]
            status.bottom_limit = bool(data[7] & 0x01)
            status.top_limit = bool(data[7] & 0x02)
            # Servo
            # bit 0: is_connected, bit 1: is_enabled
            motor_status_byte = data[8]
            status.servo_connected = bool(motor_status_byte & 0x01)
            status.servo_enabled = bool(motor_status_byte & 0x02)
            status.servo_current_alarm = struct.unpack("<H", data[9:11])[0]
            status.servo_position = struct.unpack("<i", data[11:15])[0]
            # Kinematics (float values)
            status.position_mm = struct.unpack("<f", data[15:19])[0]
            status.velocity_mm = struct.unpack("<f", data[19:23])[0]
            status.torque = struct.unpack("<f", data[23:27])[0]
            # Motor status (int16 values)
            status.motor_current = struct.unpack("<h", data[27:29])[0]
            status.voltage = struct.unpack("<h", data[29:31])[0]
            status.temperature = struct.unpack("<h", data[31:33])[0]

        status.last_update = datetime.now()
        return status

    def _parse_wally_status(self, data: bytes) -> WallyStatus:
        """Parse Wally system status.

        v1-p1: 106 bytes (ToF with float distance)
        v1-p2: 80 bytes (compact motor status 13B each)
        """
        # Determine actual format based on data length
        # v1-p2 needs 49+ bytes, v1-p1 needs 60+ bytes
        use_v2_format = self.profile_id == "v1-p2" and len(data) >= 49

        # Update profile_id if format doesn't match (for frontend UI)
        if self.profile_id == "v1-p2" and not use_v2_format:
            print(f"[BLE] Wally: Data format mismatch ({len(data)} bytes), switching to v1-p1 UI")
            self.profile_id = "v1-p1"

        if use_v2_format:
            return self._parse_wally_status_v2(data)
        else:
            return self._parse_wally_status_v1(data)

    def _parse_wally_status_v1(self, data: bytes) -> WallyStatus:
        """Parse Wally v1-p1 format (106 bytes)."""
        status = WallyStatus()

        if len(data) < 60:
            return status

        status.motion_state = MotionState(data[0])
        # ToF sensors: status byte + distance (float)
        tof_left_status = data[1]
        tof_left_dist = struct.unpack("<f", data[2:6])[0]
        status.tof_left = WallyTofStatus.from_bytes_v1(tof_left_status, tof_left_dist)

        tof_right_status = data[6]
        tof_right_dist = struct.unpack("<f", data[7:11])[0]
        status.tof_right = WallyTofStatus.from_bytes_v1(tof_right_status, tof_right_dist)

        # Limit switch
        status.limit_switch_state = data[11]

        # Left motor (bytes 12-35)
        status.motor_left.current_alarm = struct.unpack("<H", data[12:14])[0]
        status.motor_left.position = struct.unpack("<i", data[14:18])[0]
        status.motor_left.position_mm = struct.unpack("<f", data[18:22])[0]
        status.motor_left.velocity = struct.unpack("<f", data[22:26])[0]
        status.motor_left.torque = struct.unpack("<f", data[26:30])[0]
        status.motor_left.current = struct.unpack("<h", data[30:32])[0]
        status.motor_left.voltage = struct.unpack("<h", data[32:34])[0]
        status.motor_left.temperature = struct.unpack("<h", data[34:36])[0]

        # Right motor (bytes 36-59)
        status.motor_right.current_alarm = struct.unpack("<H", data[36:38])[0]
        status.motor_right.position = struct.unpack("<i", data[38:42])[0]
        status.motor_right.position_mm = struct.unpack("<f", data[42:46])[0]
        status.motor_right.velocity = struct.unpack("<f", data[46:50])[0]
        status.motor_right.torque = struct.unpack("<f", data[50:54])[0]
        status.motor_right.current = struct.unpack("<h", data[54:56])[0]
        status.motor_right.voltage = struct.unpack("<h", data[56:58])[0]
        status.motor_right.temperature = struct.unpack("<h", data[58:60])[0]

        # Wally kinematics (bytes 60+)
        if len(data) >= 90:
            status.wally_x = struct.unpack("<f", data[60:64])[0]
            status.wally_y = struct.unpack("<f", data[64:68])[0]
            status.distance_to_wall = struct.unpack("<h", data[68:70])[0]
            status.angle = struct.unpack("<d", data[70:78])[0]
            status.target_x = struct.unpack("<f", data[78:82])[0]
            status.target_y = struct.unpack("<f", data[82:86])[0]
            status.target_velocity = struct.unpack("<f", data[86:90])[0]

        status.last_update = datetime.now()
        return status

    def _parse_wally_status_v2(self, data: bytes) -> WallyStatus:
        """Parse Wally v1-p2 format (80 bytes, compact motor 13B each)."""
        status = WallyStatus()


        if len(data) < 49:
            return status

        # Common (17 bytes, offset 0)
        status.motion_state = MotionState(data[0])
        status.mcu_temp = struct.unpack("<b", data[1:2])[0]  # int8
        status.speed_control_state = data[2]
        status.position_percentage = data[3]
        status.position_mm = struct.unpack("<h", data[4:6])[0]  # signed int16
        status.remain_distance = struct.unpack("<h", data[6:8])[0]  # signed int16
        status.torque = struct.unpack("<h", data[8:10])[0]  # signed int16
        status.current_velocity = struct.unpack("<h", data[10:12])[0]  # signed int16
        status.command_velocity = struct.unpack("<h", data[12:14])[0]  # signed int16
        status.is_position_verified = bool(data[14])
        status.is_current_model_learning = bool(data[15])
        status.motion_phase = data[16]

        # Sensors (6 bytes, offset 17)
        status.tof_left = WallyTofStatus.from_bytes_v2(data[17], data[18])
        status.tof_right = WallyTofStatus.from_bytes_v2(data[19], data[20])
        status.limit_switch_state = data[21]
        status.photo_sensor_state = data[22]

        # Left motor (13 bytes, offset 23)
        # bit 0: is_connected, bit 1: is_enabled
        ml_status_byte = data[23]
        status.motor_left.is_connected = bool(ml_status_byte & 0x01)
        status.motor_left.is_enabled = bool(ml_status_byte & 0x02)
        status.motor_left.current_alarm = struct.unpack("<H", data[24:26])[0]
        status.motor_left.raw_velocity = struct.unpack("<h", data[26:28])[0]
        status.motor_left.raw_torque = struct.unpack("<h", data[28:30])[0]
        status.motor_left.current = struct.unpack("<h", data[30:32])[0]
        status.motor_left.voltage = struct.unpack("<h", data[32:34])[0]
        status.motor_left.temperature = struct.unpack("<h", data[34:36])[0]

        # Right motor (13 bytes, offset 36)
        # bit 0: is_connected, bit 1: is_enabled
        mr_status_byte = data[36]
        status.motor_right.is_connected = bool(mr_status_byte & 0x01)
        status.motor_right.is_enabled = bool(mr_status_byte & 0x02)
        status.motor_right.current_alarm = struct.unpack("<H", data[37:39])[0]
        status.motor_right.raw_velocity = struct.unpack("<h", data[39:41])[0]
        status.motor_right.raw_torque = struct.unpack("<h", data[41:43])[0]
        status.motor_right.current = struct.unpack("<h", data[43:45])[0]
        status.motor_right.voltage = struct.unpack("<h", data[45:47])[0]
        status.motor_right.temperature = struct.unpack("<h", data[47:49])[0]

        # Wally kinematics (31 bytes, offset 49)
        if len(data) >= 67:
            status.wally_x = struct.unpack("<f", data[49:53])[0]
            status.wally_y = struct.unpack("<f", data[53:57])[0]
            status.distance_to_wall = struct.unpack("<h", data[57:59])[0]
            status.angle = struct.unpack("<d", data[59:67])[0]
            # Reserved 13 bytes (offset 67-79)

        status.last_update = datetime.now()
        return status

    async def read_status(self) -> Optional[DeviceStatus]:
        """Read device status."""
        if not self.connected:
            return None

        try:
            data = await self.client.read_gatt_char(CharUUID.SYSTEM_STATUS)
            self.last_packet_time = datetime.now()

            if self.device_type == "ceily":
                self.status = self._parse_ceily_status(data)
            elif self.device_type == "wally":
                self.status = self._parse_wally_status(data)

            if self.on_status_update and self.status:
                self.on_status_update(self.status)

            return self.status

        except Exception:
            self.command_error_count += 1
            return None

    async def subscribe_status(self) -> bool:
        """Subscribe to status notifications (v1-p2 notify mode).

        Returns True if successfully subscribed.
        """
        if not self.connected:
            return False

        if self._status_subscribed:
            return True

        try:
            await self.client.start_notify(
                CharUUID.SYSTEM_STATUS,
                self._handle_status_notification,
            )
            self._status_subscribed = True
            return True
        except Exception:
            return False

    async def unsubscribe_status(self) -> bool:
        """Unsubscribe from status notifications.

        Returns True if successfully unsubscribed.
        """
        if not self.connected:
            return False

        if not self._status_subscribed:
            return True

        try:
            await self.client.stop_notify(CharUUID.SYSTEM_STATUS)
            self._status_subscribed = False
            return True
        except Exception:
            return False

    @property
    def status_subscribed(self) -> bool:
        """Return whether status notifications are subscribed."""
        return self._status_subscribed

    async def send_command(self, command: MotionCommand) -> bool:
        """Send motion command (UP/DOWN/STOP)."""
        if not self.connected:
            return False

        try:
            data = build_motion_command(command)
            await self.client.write_gatt_char(CharUUID.MOTION_CONTROL, data)
            self.command_success_count += 1
            self.last_packet_time = datetime.now()
            return True
        except Exception:
            self.command_error_count += 1
            return False

    async def send_up(self) -> bool:
        """Send UP/OPEN command."""
        return await self.send_command(MotionCommand.UP)

    async def send_down(self) -> bool:
        """Send DOWN/CLOSE command."""
        return await self.send_command(MotionCommand.DOWN)

    async def send_stop(self) -> bool:
        """Send STOP command."""
        return await self.send_command(MotionCommand.STOP)

    async def set_led_brightness(self, target: LEDTarget, brightness: int) -> bool:
        """Set LED brightness (0-255)."""
        if not self.connected:
            return False

        try:
            data = build_led_brightness(target, brightness)
            await self.client.write_gatt_char(CharUUID.LED_CONTROL, data)
            self.command_success_count += 1
            return True
        except Exception:
            self.command_error_count += 1
            return False

    async def set_led_color_index(self, index: int) -> bool:
        """Set LED color by index."""
        if not self.connected:
            return False

        try:
            data = build_led_color_index(index)
            await self.client.write_gatt_char(CharUUID.LED_CONTROL, data)
            self.command_success_count += 1
            return True
        except Exception:
            self.command_error_count += 1
            return False

    async def reset_torque_model(self) -> bool:
        """Reset torque model."""
        if not self.connected:
            return False

        try:
            data = build_torque_command(TorqueCommand.RESET_MODEL)
            await self.client.write_gatt_char(CharUUID.TORQUE_CONTROL, data)
            self.command_success_count += 1
            return True
        except Exception:
            self.command_error_count += 1
            return False

    async def save_torque_model(self) -> bool:
        """Save torque model."""
        if not self.connected:
            return False

        try:
            data = build_torque_command(TorqueCommand.SAVE_MODEL)
            await self.client.write_gatt_char(CharUUID.TORQUE_CONTROL, data)
            self.command_success_count += 1
            return True
        except Exception:
            self.command_error_count += 1
            return False

    async def read_dimension(self, dimension_id: int) -> Optional[int]:
        """Read dimension value."""
        if not self.connected:
            return None

        try:
            data = build_dimension_write(dimension_id, 0)
            await self.client.write_gatt_char(CharUUID.DIMENSION, data)
            result = await self.client.read_gatt_char(CharUUID.DIMENSION)
            if len(result) >= 8:
                _, value = struct.unpack("<II", result[:8])
                return value
            return None
        except Exception:
            self.command_error_count += 1
            return None

    async def write_dimension(self, dimension_id: int, value: int) -> bool:
        """Write dimension value."""
        if not self.connected:
            return False

        try:
            data = build_dimension_write(dimension_id, value)
            await self.client.write_gatt_char(CharUUID.DIMENSION, data)
            self.command_success_count += 1
            return True
        except Exception:
            self.command_error_count += 1
            return False

    async def save_dimensions(self) -> bool:
        """Save all dimensions to flash."""
        if not self.connected:
            return False

        try:
            data = build_dimension_write(DimensionCommand.SAVE, 0)
            await self.client.write_gatt_char(CharUUID.DIMENSION, data)
            self.command_success_count += 1
            return True
        except Exception:
            self.command_error_count += 1
            return False

    async def set_wifi_config(self, ssid: str, password: str) -> bool:
        """Set WiFi configuration."""
        if not self.connected:
            return False

        try:
            data = build_wifi_config(ssid, password)
            await self.client.write_gatt_char(CharUUID.WIFI_CONFIG, data)
            self.command_success_count += 1
            return True
        except Exception:
            self.command_error_count += 1
            return False

    async def read_wifi_status(self) -> Optional[dict]:
        """Read WiFi configuration status (33 bytes: 32 SSID + 1 status)."""
        if not self.connected:
            return None

        try:
            data = await self.client.read_gatt_char(CharUUID.WIFI_CONFIG)
            from .protocol import parse_wifi_status
            return parse_wifi_status(data)
        except Exception:
            self.command_error_count += 1
            return None

    async def read_device_info(self) -> Optional[dict]:
        """Read Device Information Service (BLE SIG 0x180A).

        Returns dict with:
        - manufacturer_name: e.g., "Rovothome"
        - model_number: e.g., "ceily-p2" or "wally-p2"
        - serial_number: e.g., "1234567890123456"
        - hardware_revision: e.g., "v1"
        - firmware_revision: e.g., "1.0.1"
        - protocol_version: parsed from model_number (e.g., 2)
        """
        if not self.connected:
            return None

        result = {
            "manufacturer_name": None,
            "model_number": None,
            "serial_number": None,
            "hardware_revision": None,
            "firmware_revision": None,
            "protocol_version": None,
        }

        try:
            # Read Manufacturer Name (e.g., "Rovothome")
            data = await self.client.read_gatt_char(CharUUID.MANUFACTURER_NAME)
            result["manufacturer_name"] = data.decode("utf-8").rstrip("\x00")
        except Exception as e:
            print(f"[BLE] Failed to read manufacturer_name: {e}")

        try:
            # Read Model Number (e.g., "ceily-p2")
            data = await self.client.read_gatt_char(CharUUID.MODEL_NUMBER)
            result["model_number"] = data.decode("utf-8").rstrip("\x00")
            # Parse protocol version from model number (e.g., "ceily-p2" -> 2)
            if "-p" in result["model_number"]:
                try:
                    result["protocol_version"] = int(
                        result["model_number"].split("-p")[1]
                    )
                except (ValueError, IndexError):
                    pass
        except Exception as e:
            print(f"[BLE] Failed to read model_number: {e}")

        try:
            # Read Serial Number (e.g., "1234567890123456")
            data = await self.client.read_gatt_char(CharUUID.SERIAL_NUMBER)
            result["serial_number"] = data.decode("utf-8").rstrip("\x00")
        except Exception as e:
            print(f"[BLE] Failed to read serial_number: {e}")

        try:
            # Read Hardware Revision (e.g., "v1")
            data = await self.client.read_gatt_char(CharUUID.HARDWARE_REVISION)
            result["hardware_revision"] = data.decode("utf-8").rstrip("\x00")
        except Exception as e:
            print(f"[BLE] Failed to read hardware_revision: {e}")

        try:
            # Read Firmware Revision (e.g., "1.0.1")
            data = await self.client.read_gatt_char(CharUUID.FIRMWARE_REVISION)
            result["firmware_revision"] = data.decode("utf-8").rstrip("\x00")
        except Exception as e:
            print(f"[BLE] Failed to read firmware_revision: {e}")

        self.last_packet_time = datetime.now()
        print(f"[BLE] Device info result: {result}")
        return result

    async def read_all_dimensions(self) -> Optional[dict]:
        """Read all dimensions from device."""
        if not self.connected:
            return None

        try:
            data = await self.client.read_gatt_char(CharUUID.DIMENSION)
            self.last_packet_time = datetime.now()

            if self.device_type == "ceily":
                from .protocol import parse_ceily_dimensions, CEILY_DIMENSIONS
                values = parse_ceily_dimensions(data)
                return {
                    "device_type": "ceily",
                    "dimensions": [
                        {
                            "id": dim["id"],
                            "name": dim["name"],
                            "unit": dim["unit"],
                            "type": dim["type"],
                            "value": values.get(dim["id"], 0),
                            "readonly": dim.get("readonly", False),
                        }
                        for dim in CEILY_DIMENSIONS
                    ],
                }
            elif self.device_type == "wally":
                from .protocol import parse_wally_dimensions, WALLY_DIMENSIONS
                values = parse_wally_dimensions(data)
                return {
                    "device_type": "wally",
                    "dimensions": [
                        {
                            "id": dim["id"],
                            "name": dim["name"],
                            "unit": dim["unit"],
                            "type": dim["type"],
                            "value": values.get(dim["id"], 0),
                            "readonly": dim.get("readonly", False),
                        }
                        for dim in WALLY_DIMENSIONS
                    ],
                }
            return None
        except Exception:
            self.command_error_count += 1
            return None

    def get_stats(self) -> dict:
        """Get command statistics."""
        total = self.command_success_count + self.command_error_count
        success_rate = (
            (self.command_success_count / total * 100) if total > 0 else 0
        )
        return {
            "success_count": self.command_success_count,
            "error_count": self.command_error_count,
            "success_rate": round(success_rate, 1),
        }

    def get_connection_info(self) -> dict:
        """Get current connection info."""
        info = {
            "connected": self.connected,
            "state": self.connection_state.value,
            "device_name": self.device_name,
            "device_address": self.device_address,
            "device_type": self.device_type,
            "profile_id": self.profile_id,
            "rssi": self.rssi,
            "last_packet": (
                self.last_packet_time.isoformat()
                if self.last_packet_time else None
            ),
        }
        if self.device_info:
            info["device_info"] = self.device_info
        return info
