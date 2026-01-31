"""ISV2 serial protocol implementation (Modbus RTU based)."""

import struct
import time
from typing import List, Optional

from .serial_port import SerialPort


class ISV2Error(Exception):
    """Base exception for ISV2 protocol errors."""
    pass


class ISV2TimeoutError(ISV2Error):
    """Response timeout error."""
    pass


class ISV2CRCError(ISV2Error):
    """CRC checksum mismatch error."""
    pass


class ISV2ResponseError(ISV2Error):
    """Invalid response error."""
    pass


def calculate_crc16(data: bytes) -> int:
    """Calculate CRC16-Modbus checksum.

    Args:
        data: Input bytes

    Returns:
        CRC16 value (16-bit)
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def build_read_request(addr: int, reg_addr: int, count: int) -> bytes:
    """Build read registers request frame (Function 0x03).

    Args:
        addr: Device address
        reg_addr: Register address
        count: Number of registers to read

    Returns:
        Request frame bytes
    """
    frame = struct.pack(">BBHH", addr, 0x03, reg_addr, count)
    crc = calculate_crc16(frame)
    frame += struct.pack("<H", crc)  # CRC is little-endian
    return frame


def build_write16_request(addr: int, reg_addr: int, value: int) -> bytes:
    """Build write single register request frame (Function 0x06).

    Args:
        addr: Device address
        reg_addr: Register address
        value: 16-bit value to write

    Returns:
        Request frame bytes
    """
    frame = struct.pack(">BBHH", addr, 0x06, reg_addr, value)
    crc = calculate_crc16(frame)
    frame += struct.pack("<H", crc)
    return frame


def build_write32_request(addr: int, reg_addr: int, value: int) -> bytes:
    """Build write 32-bit parameter request frame (Function 0x10 - Write Multiple).

    32-bit value stored as two 16-bit registers:
    - High 16-bit at even address
    - Low 16-bit at odd address

    Frame format: [addr][0x10][reg_hi][reg_lo][num_h][num_l][byte_count][data...][crc]

    Args:
        addr: Device address
        reg_addr: Register address
        value: 32-bit value to write

    Returns:
        Request frame bytes
    """
    high_word = (value >> 16) & 0xFFFF
    low_word = value & 0xFFFF
    # [addr][0x10][reg_addr(2)][num_regs(2)][byte_count][high_word][low_word]
    frame = struct.pack(">BBHHB", addr, 0x10, reg_addr, 2, 4)  # 2 regs, 4 bytes
    frame += struct.pack(">HH", high_word, low_word)
    crc = calculate_crc16(frame)
    frame += struct.pack("<H", crc)
    return frame


def parse_read_response(data: bytes, expected_addr: int) -> List[int]:
    """Parse read response frame.

    Response format: [addr][func][byte_count][data...][crc_lo][crc_hi]

    Args:
        data: Response bytes
        expected_addr: Expected device address

    Returns:
        List of 16-bit register values

    Raises:
        ISV2ResponseError: Invalid response format
        ISV2CRCError: CRC mismatch
    """
    if len(data) < 5:
        raise ISV2ResponseError(f"Response too short: {len(data)} bytes")

    addr, func, byte_count = struct.unpack(">BBB", data[:3])

    if addr != expected_addr:
        raise ISV2ResponseError(f"Address mismatch: expected {expected_addr}, got {addr}")

    if func == 0x83:  # Error response
        error_code = data[2] if len(data) > 2 else 0
        raise ISV2ResponseError(f"Device error: 0x{error_code:02X}")

    if func != 0x03:
        raise ISV2ResponseError(f"Unexpected function code: 0x{func:02X}")

    expected_len = 3 + byte_count + 2  # header + data + crc
    if len(data) < expected_len:
        raise ISV2ResponseError(f"Response incomplete: expected {expected_len}, got {len(data)}")

    # Verify CRC
    payload = data[:3 + byte_count]
    received_crc = struct.unpack("<H", data[3 + byte_count:3 + byte_count + 2])[0]
    calculated_crc = calculate_crc16(payload)

    if received_crc != calculated_crc:
        raise ISV2CRCError(f"CRC mismatch: expected 0x{calculated_crc:04X}, got 0x{received_crc:04X}")

    # Extract register values
    values = []
    for i in range(0, byte_count, 2):
        value = struct.unpack(">H", data[3 + i:3 + i + 2])[0]
        values.append(value)

    return values


def parse_write_response(data: bytes, expected_addr: int) -> bool:
    """Parse write response frame (echo response or error).

    Args:
        data: Response bytes
        expected_addr: Expected device address

    Returns:
        True if write successful

    Raises:
        ISV2ResponseError: Invalid response
        ISV2CRCError: CRC mismatch
    """
    if len(data) < 5:
        raise ISV2ResponseError(f"Response too short: {len(data)} bytes")

    addr, func = struct.unpack(">BB", data[:2])

    if addr != expected_addr:
        raise ISV2ResponseError(f"Address mismatch: expected {expected_addr}, got {addr}")

    # Error response: [ID][FC+0x80][ERROR_CODE][CRC_L][CRC_H] = 5 bytes
    if func & 0x80:
        error_codes = {
            0x01: "Function code error",
            0x02: "Address error",
            0x03: "Data error (value out of range)",
            0x08: "CRC checksum error",
        }
        error_code = data[2] if len(data) > 2 else 0
        error_msg = error_codes.get(error_code, f"Unknown error")
        raise ISV2ResponseError(f"Device error 0x{error_code:02X}: {error_msg}")

    # Normal response - verify CRC
    payload = data[:-2]
    received_crc = struct.unpack("<H", data[-2:])[0]
    calculated_crc = calculate_crc16(payload)

    if received_crc != calculated_crc:
        raise ISV2CRCError(f"CRC mismatch: expected 0x{calculated_crc:04X}, got 0x{received_crc:04X}")

    return True


class ISV2Client:
    """ISV2 motor communication client."""

    def __init__(
        self,
        port: str,
        device_addr: int = 0x11,
        baudrate: int = 38400,
        timeout: float = 0.2,
        retries: int = 3,
        verbose: bool = False,
    ):
        self.device_addr = device_addr
        self.retries = retries
        self.verbose = verbose
        self._serial = SerialPort(port, baudrate, timeout)

    def open(self) -> bool:
        """Open connection."""
        return self._serial.open()

    def close(self) -> None:
        """Close connection."""
        self._serial.close()

    def __enter__(self) -> "ISV2Client":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _send_receive(self, request: bytes, response_size: int) -> bytes:
        """Send request and receive response with retry logic."""
        last_error: Optional[Exception] = None

        for attempt in range(self.retries):
            try:
                self._serial.flush()

                if self.verbose:
                    print(f"TX: {request.hex(' ').upper()}")

                self._serial.write(request)
                time.sleep(0.01)  # Small delay before reading

                response = self._serial.read(response_size)

                if self.verbose:
                    print(f"RX: {response.hex(' ').upper()}")

                if len(response) == 0:
                    raise ISV2TimeoutError("No response received")

                return response

            except (ISV2TimeoutError, ISV2CRCError) as e:
                last_error = e
                if attempt < self.retries - 1:
                    time.sleep(0.05)
                    continue
                raise

        raise last_error or ISV2TimeoutError("Communication failed")

    def read(self, reg_addr: int, count: int = 1) -> List[int]:
        """Read registers from device.

        Args:
            reg_addr: Starting register address
            count: Number of registers to read

        Returns:
            List of 16-bit register values
        """
        request = build_read_request(self.device_addr, reg_addr, count)
        response_size = 5 + count * 2  # header(3) + data(n*2) + crc(2)
        response = self._send_receive(request, response_size)
        return parse_read_response(response, self.device_addr)

    def write16(self, reg_addr: int, value: int) -> bool:
        """Write 16-bit value to register.

        Args:
            reg_addr: Register address
            value: 16-bit value

        Returns:
            True if successful
        """
        request = build_write16_request(self.device_addr, reg_addr, value)
        response = self._send_receive(request, 8)
        return parse_write_response(response, self.device_addr)

    def write32(self, reg_addr: int, value: int) -> bool:
        """Write 32-bit value to register (Function 0x10 - Write Multiple).

        Args:
            reg_addr: Register address
            value: 32-bit value

        Returns:
            True if successful
        """
        request = build_write32_request(self.device_addr, reg_addr, value)
        response = self._send_receive(request, 8)  # Response: [ID][0x10][addr][num][crc]
        return parse_write_response(response, self.device_addr)

    def save(self) -> bool:
        """Save parameters to EEPROM.

        Control word 0x2211 to register 0x1801
        """
        return self.write16(self.CONTROL_WORD_REG, self.CONTROL_WORDS["save"])

    # Alarm codes mapping
    ALARM_CODES = {
        0x000: "Normal",
        0x0E1: "Overcurrent",
        0x0E0: "Overcurrent",
        0x100: "Overload",
        0x180: "Excessive position deviation",
        0x1A0: "Overspeed",
        0x1A1: "Motor out of control",
        0x0D0: "Undervoltage",
        0x0C0: "Overvoltage",
        0x190: "Excessive motor vibration",
        0x150: "Encoder disconnected",
        0x151: "Encoder data error",
        0x170: "Encoder data error",
        0x152: "Encoder HALL signal error",
        0x240: "Parameter saving error",
        0x570: "Emergency stop",
        0x120: "Regenerative energy overload",
        0x171: "Encoder parameter error",
        0x172: "Encoder parameter error",
        0x210: "Input configuration error",
        0x211: "Input configuration error",
        0x212: "Input configuration error",
    }

    def read_status(self) -> dict:
        """Read motor status.

        Returns:
            Status dictionary with enable info
        """
        # Read status flags (0x9E14) - from packet capture
        status_regs = self.read(0x9E14, 1)
        status = status_regs[0]

        return {
            "status_raw": status,
            "enabled": bool(status & 0x02),  # Bit 1 = enable
            "ready": bool(status & 0x01),    # Bit 0 = ready
            "alarm": bool(status & 0x08),    # Bit 3 = alarm
        }

    # Parameter registers with value mappings
    # Note: RS232 tuning port uses different addresses than RS485
    PARAMS = {
        "Pr5.29": {
            "addr": 0x02BA,  # RS232 address (RS485: 0x053B)
            "name": "Comm Format",
            "bits": 32,
            "mapping": {
                0: "8E2",
                1: "8O2",
                2: "8E1",
                3: "8O1",
                4: "8N1",
                5: "8N2 (Default)",
            },
        },
        "Pr5.30": {
            "addr": 0x02BC,  # RS232 address (RS485: 0x053D)
            "name": "Baud Rate",
            "bits": 32,
            "mapping": {
                0: "2400 bps",
                1: "4800 bps",
                2: "9600 bps",
                3: "19200 bps",
                4: "38400 bps (Default)",
                5: "57600 bps",
                6: "115200 bps",
            },
        },
        "Pr5.31": {
            "addr": 0x02BE,  # RS232 address (RS485: 0x053F)
            "name": "Slave ID",
            "bits": 32,
            "mapping": None,  # Direct value (0-127, default 1)
        },
    }

    # Control word register
    # RS232: 0x7200, RS485: 0x1801
    CONTROL_WORD_REG = 0x7200
    CONTROL_WORDS = {
        "save": 0x1124,           # RS232 (packet capture)
        "factory_reset": 0x1234,  # RS232 (estimated)
        # RS485 values: save=0x2211, factory_reset=0x2233
    }

    # Baud rate register and value mapping
    BAUD_RATE_REG = 0x02BC  # Pr5.30 (RS232 address)
    BAUD_RATES = {
        0: 2400,
        1: 4800,
        2: 9600,
        3: 19200,
        4: 38400,
        5: 57600,
        6: 115200,
    }

    def read_param(self, param_name: str) -> dict:
        """Read a named parameter.

        Args:
            param_name: Parameter name (e.g., "Pr0.01", "Pr5.30")

        Returns:
            Dict with param info and value
        """
        if param_name not in self.PARAMS:
            raise ISV2Error(f"Unknown parameter: {param_name}")

        param = self.PARAMS[param_name]
        regs = self.read(param["addr"], 2)
        value = (regs[0] << 16) | regs[1]

        # Get mapped value if mapping exists
        mapped = None
        if param.get("mapping"):
            mapped = param["mapping"].get(value, f"Unknown ({value})")
        else:
            mapped = str(value)

        return {
            "name": param_name,
            "description": param["name"],
            "value": value,
            "mapped": mapped,
        }

    def read_all_params(self) -> list:
        """Read all defined parameters.

        Returns:
            List of parameter dicts
        """
        results = []
        for param_name in self.PARAMS:
            try:
                result = self.read_param(param_name)
                results.append(result)
            except ISV2Error as e:
                results.append({
                    "name": param_name,
                    "error": str(e),
                })
        return results

    def write_param(self, param_name: str, value: int) -> bool:
        """Write a named parameter.

        Args:
            param_name: Parameter name (e.g., "Pr0.01", "Pr5.30")
            value: Value to write

        Returns:
            True if successful
        """
        if param_name not in self.PARAMS:
            raise ISV2Error(f"Unknown parameter: {param_name}")

        param = self.PARAMS[param_name]
        return self.write32(param["addr"], value)

    def read_baudrate(self) -> dict:
        """Read current baud rate setting.

        Returns:
            Dict with raw value and actual baud rate
        """
        regs = self.read(self.BAUD_RATE_REG, 2)
        value = (regs[0] << 16) | regs[1]
        baudrate = self.BAUD_RATES.get(value, None)
        return {
            "value": value,
            "baudrate": baudrate,
        }

    def set_baudrate(self, value: int) -> bool:
        """Set baud rate (0-4).

        Args:
            value: 0=9600, 1=19200, 2=38400, 3=57600, 4=115200

        Returns:
            True if successful
        """
        if value not in self.BAUD_RATES:
            raise ISV2Error(f"Invalid baud rate value: {value}")
        return self.write32(self.BAUD_RATE_REG, value)

    def is_enabled(self) -> bool:
        """Check if motor is enabled.

        Returns:
            True if motor is enabled
        """
        status = self.read_status()
        return status["enabled"]

    def factory_reset(self, force: bool = False) -> bool:
        """Factory reset - restore default parameters.

        Args:
            force: If False, check enable status first

        Returns:
            True if successful

        Raises:
            ISV2Error: If motor is enabled and force=False
        """
        if not force and self.is_enabled():
            raise ISV2Error("Motor is enabled. Disable first or use force=True")

        return self.write16(self.CONTROL_WORD_REG, self.CONTROL_WORDS["factory_reset"])
