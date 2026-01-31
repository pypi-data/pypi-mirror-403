"""BLE GATT Protocol Definitions for Ceily/Wally devices."""

from enum import IntEnum

# Device prefixes for scanning
DEVICE_PREFIX_CEILY = "ceily-"
DEVICE_PREFIX_WALLY = "wally-"


# =============================================================================
# Service UUIDs
# =============================================================================

class ServiceUUID:
    """BLE Service UUIDs."""
    # BLE SIG Standard Services
    DEVICE_INFO = "0000180a-0000-1000-8000-00805f9b34fb"  # 16-bit: 0x180A
    # Custom Services
    CONTROL = "0000ff20-0000-1000-8000-00805f9b34fb"  # 16-bit: 0xFF20
    SYSTEM_STATUS = "501a8cf5-98a7-4370-bb97-632c84910000"
    DIMENSION = "cc9762a6-bbb7-4b21-b2e2-153059030000"
    TORQUE = "acc2a064-99f7-404e-a7df-b1714f3d0000"
    LED = "07ecc81b-b952-47e6-a1f1-0999577f0000"
    LOG = "cc9762a6-bbb7-4b21-b2e2-153059032200"


# =============================================================================
# Characteristic UUIDs
# =============================================================================

class CharUUID:
    """BLE Characteristic UUIDs."""
    # Device Information Service (Read) - BLE SIG Standard
    MANUFACTURER_NAME = "00002a29-0000-1000-8000-00805f9b34fb"  # 16-bit: 0x2A29
    MODEL_NUMBER = "00002a24-0000-1000-8000-00805f9b34fb"  # 16-bit: 0x2A24
    SERIAL_NUMBER = "00002a25-0000-1000-8000-00805f9b34fb"  # 16-bit: 0x2A25
    HARDWARE_REVISION = "00002a27-0000-1000-8000-00805f9b34fb"  # 16-bit: 0x2A27
    FIRMWARE_REVISION = "00002a26-0000-1000-8000-00805f9b34fb"  # 16-bit: 0x2A26

    # Motion Control (Write)
    MOTION_CONTROL = "0000ff21-0000-1000-8000-00805f9b34fb"  # 16-bit: 0xFF21

    # System Status (Read/Notify)
    SYSTEM_STATUS = "501a8cf5-98a7-4370-bb97-632c84910001"

    # Dimension (Read/Write)
    DIMENSION = "cc9762a6-bbb7-4b21-b2e2-153059030001"

    # Torque Control (Write)
    TORQUE_CONTROL = "acc2a064-99f7-404e-a7df-b1714f3d00fd"
    # Torque Status (Read)
    TORQUE_STATUS_1 = "acc2a064-99f7-404e-a7df-b1714f3d0001"
    TORQUE_STATUS_2 = "acc2a064-99f7-404e-a7df-b1714f3d0002"
    TORQUE_GRAPH = "acc2a064-99f7-404e-a7df-b1714f3d0010"

    # LED Control (Write)
    LED_CONTROL = "07ecc81b-b952-47e6-a1f1-0999577f0001"
    # LED Status (Read)
    LED_STATUS = "07ecc81b-b952-47e6-a1f1-0999577f0002"

    # Log Event (Notify)
    LOG_EVENT = "cc9762a6-bbb7-4b21-b2e2-153059032201"

    # WiFi Provisioning (Read/Write)
    WIFI_CONFIG = "0caaae86-33a2-4f8e-93d2-4de5c6a900af"


# =============================================================================
# Motion Commands
# =============================================================================

class MotionCommand(IntEnum):
    """Motion control commands (for MOTION_CONTROL characteristic)."""
    STOP = 0x00
    UP = 0x01      # Ceily: Up, Wally: Open
    DOWN = 0x02    # Ceily: Down, Wally: Close

    # Aliases for Wally
    OPEN = 0x01
    CLOSE = 0x02


# =============================================================================
# Motion State
# =============================================================================

class MotionState(IntEnum):
    """Device motion state (from SYSTEM_STATUS characteristic byte 0)."""
    DOWN = 0       # Ceily: Down position, Wally: Closed
    UP = 1         # Ceily: Up position, Wally: Opened
    MOVING_DOWN = 2
    MOVING_UP = 3
    STOP = 4
    EMERGENCY = 5
    INIT = 255


# =============================================================================
# LED Commands
# =============================================================================

class LEDCommand(IntEnum):
    """LED control commands."""
    NONE = 0
    CHANGE_MODE = 1
    CHANGE_BRIGHTNESS = 2
    CHANGE_RGB_INDEX = 3
    CHANGE_COLOR = 4


class LEDTarget(IntEnum):
    """LED target index."""
    MAIN = 0
    HEAD = 1
    MOOD = 3


# =============================================================================
# Torque Commands
# =============================================================================

class TorqueCommand(IntEnum):
    """Torque model control commands."""
    SET_SENSITIVITY = 0x11
    RESET_MODEL = 0xA4
    SAVE_MODEL = 0xEA


# =============================================================================
# Dimension Commands and IDs
# =============================================================================

class DimensionCommand(IntEnum):
    """Dimension save command."""
    SAVE = 0xFD


class CeilyDimensionID(IntEnum):
    """Ceily dimension IDs."""
    WIDTH_MM = 0x01
    LENGTH_MM = 0x02
    STROKE_MM = 0x03
    GEAR_RATIO = 0x04
    PULLEY_RADIUS_MM = 0x05


class WallyDimensionID(IntEnum):
    """Wally dimension IDs."""
    OPEN_LIMIT_DISTANCE_MM = 0x01
    LEFT_WHEEL_FROM_TOF_MM = 0x04
    RIGHT_WHEEL_FROM_TOF_MM = 0x05
    LEFT_TOF_OFFSET_FROM_CENTER_MM = 0x06
    RIGHT_TOF_OFFSET_FROM_CENTER_MM = 0x07
    TOF_Y_OFFSET_FROM_CENTER_MM = 0x08
    IS_OPEN_PLUS_DIRECTION = 0x09
    WHEEL_RADIUS_MM = 0x0A
    GEAR_RATIO = 0x0B
    KEEP_DISTANCE_MM = 0x0C
    MISSION_SPEED = 0x0D
    CONTROL_BUTTON_VERSION = 0xEE


# Dimension metadata for UI display
CEILY_DIMENSIONS = [
    {"id": CeilyDimensionID.WIDTH_MM, "name": "Width", "unit": "mm", "type": "uint16"},
    {"id": CeilyDimensionID.LENGTH_MM, "name": "Length", "unit": "mm", "type": "uint16"},
    {"id": CeilyDimensionID.STROKE_MM, "name": "Stroke", "unit": "mm", "type": "uint16"},
    {"id": CeilyDimensionID.GEAR_RATIO, "name": "Gear Ratio", "unit": "", "type": "uint8"},
    {"id": CeilyDimensionID.PULLEY_RADIUS_MM, "name": "Pulley Radius", "unit": "mm", "type": "uint8"},
]

WALLY_DIMENSIONS = [
    {"id": WallyDimensionID.OPEN_LIMIT_DISTANCE_MM, "name": "Open Limit", "unit": "mm", "type": "uint16"},
    {"id": WallyDimensionID.LEFT_WHEEL_FROM_TOF_MM, "name": "Left Wheel from ToF", "unit": "mm", "type": "int16"},
    {"id": WallyDimensionID.RIGHT_WHEEL_FROM_TOF_MM, "name": "Right Wheel from ToF", "unit": "mm", "type": "int16"},
    {"id": WallyDimensionID.LEFT_TOF_OFFSET_FROM_CENTER_MM, "name": "Left ToF Offset", "unit": "mm", "type": "int16"},
    {"id": WallyDimensionID.RIGHT_TOF_OFFSET_FROM_CENTER_MM, "name": "Right ToF Offset", "unit": "mm", "type": "int16"},
    {"id": WallyDimensionID.TOF_Y_OFFSET_FROM_CENTER_MM, "name": "ToF Y Offset", "unit": "mm", "type": "int16"},
    {"id": WallyDimensionID.IS_OPEN_PLUS_DIRECTION, "name": "Open Plus Direction", "unit": "", "type": "bool"},
    {"id": WallyDimensionID.WHEEL_RADIUS_MM, "name": "Wheel Radius", "unit": "mm", "type": "uint8"},
    {"id": WallyDimensionID.GEAR_RATIO, "name": "Gear Ratio", "unit": "", "type": "uint8"},
    {"id": WallyDimensionID.KEEP_DISTANCE_MM, "name": "Keep Distance", "unit": "mm", "type": "uint8"},
    {"id": WallyDimensionID.MISSION_SPEED, "name": "Mission Speed", "unit": "", "type": "uint8", "readonly": True},
    {"id": WallyDimensionID.CONTROL_BUTTON_VERSION, "name": "Button Version", "unit": "", "type": "uint8", "readonly": True},
]


# =============================================================================
# Data Builders
# =============================================================================

def build_motion_command(command: MotionCommand) -> bytes:
    """Build motion control command data."""
    return bytes([command])


def build_led_brightness(target: LEDTarget, brightness: int) -> bytes:
    """Build LED brightness command (0-255)."""
    brightness = max(0, min(255, brightness))
    return bytes([LEDCommand.CHANGE_BRIGHTNESS, target, brightness])


def build_led_color_index(index: int) -> bytes:
    """Build LED color index command."""
    return bytes([LEDCommand.CHANGE_RGB_INDEX, 0x00, index])


def build_led_color_rgb(r: int, g: int, b: int) -> bytes:
    """Build LED RGB color command."""
    return bytes([LEDCommand.CHANGE_COLOR, r, g, b])


def build_torque_command(command: TorqueCommand, arg: int = 0) -> bytes:
    """Build torque control command (8 bytes: 4 cmd + 4 arg)."""
    import struct
    return struct.pack("<II", command, arg)


def build_dimension_write(dimension_id: int, value: int) -> bytes:
    """Build dimension write command (8 bytes: 4 id + 4 value)."""
    import struct
    return struct.pack("<II", dimension_id, value)


def build_wifi_config(ssid: str, password: str) -> bytes:
    """Build WiFi provisioning data (96 bytes: 32 SSID + 64 password)."""
    ssid_bytes = ssid.encode("utf-8")[:32].ljust(32, b"\x00")
    password_bytes = password.encode("utf-8")[:64].ljust(64, b"\x00")
    return ssid_bytes + password_bytes


def parse_ceily_dimensions(data: bytes) -> dict:
    """Parse Ceily dimension data (8 bytes)."""
    import struct
    if len(data) < 8:
        return {}
    width, length, stroke = struct.unpack_from("<HHH", data, 0)
    gear_ratio = data[6]
    pulley_radius = data[7]
    return {
        CeilyDimensionID.WIDTH_MM: width,
        CeilyDimensionID.LENGTH_MM: length,
        CeilyDimensionID.STROKE_MM: stroke,
        CeilyDimensionID.GEAR_RATIO: gear_ratio,
        CeilyDimensionID.PULLEY_RADIUS_MM: pulley_radius,
    }


def parse_wally_dimensions(data: bytes) -> dict:
    """Parse Wally dimension data (22 bytes)."""
    import struct
    if len(data) < 22:
        return {}
    # Bytes 0-1: open_limit_distance_mm
    # Bytes 2-5: reserved
    # Bytes 6-7: left_wheel_from_tof
    # Bytes 8-9: right_wheel_from_tof
    # Bytes 10-11: left_tof_offset_from_center
    # Bytes 12-13: right_tof_offset_from_center
    # Bytes 14-15: tof_y_offset_from_center
    # Byte 16: is_open_plus_direction
    # Byte 17: wheel_radius
    # Byte 18: gear_ratio
    # Byte 19: keep_distance
    # Byte 20: mission_speed
    # Byte 21: control_button_version
    open_limit = struct.unpack_from("<H", data, 0)[0]
    left_wheel = struct.unpack_from("<h", data, 6)[0]
    right_wheel = struct.unpack_from("<h", data, 8)[0]
    left_tof_off = struct.unpack_from("<h", data, 10)[0]
    right_tof_off = struct.unpack_from("<h", data, 12)[0]
    tof_y_off = struct.unpack_from("<h", data, 14)[0]
    is_open_plus = data[16]
    wheel_radius = data[17]
    gear_ratio = data[18]
    keep_distance = data[19]
    mission_speed = data[20]
    button_version = data[21]
    return {
        WallyDimensionID.OPEN_LIMIT_DISTANCE_MM: open_limit,
        WallyDimensionID.LEFT_WHEEL_FROM_TOF_MM: left_wheel,
        WallyDimensionID.RIGHT_WHEEL_FROM_TOF_MM: right_wheel,
        WallyDimensionID.LEFT_TOF_OFFSET_FROM_CENTER_MM: left_tof_off,
        WallyDimensionID.RIGHT_TOF_OFFSET_FROM_CENTER_MM: right_tof_off,
        WallyDimensionID.TOF_Y_OFFSET_FROM_CENTER_MM: tof_y_off,
        WallyDimensionID.IS_OPEN_PLUS_DIRECTION: is_open_plus,
        WallyDimensionID.WHEEL_RADIUS_MM: wheel_radius,
        WallyDimensionID.GEAR_RATIO: gear_ratio,
        WallyDimensionID.KEEP_DISTANCE_MM: keep_distance,
        WallyDimensionID.MISSION_SPEED: mission_speed,
        WallyDimensionID.CONTROL_BUTTON_VERSION: button_version,
    }


def parse_wifi_status(data: bytes) -> dict:
    """Parse WiFi status data (33 bytes: 32 SSID + 1 status)."""
    if len(data) < 33:
        return {"ssid": "", "connected": False}
    ssid = data[:32].rstrip(b"\x00").decode("utf-8", errors="replace")
    connected = data[32] == 1
    return {"ssid": ssid, "connected": connected}
