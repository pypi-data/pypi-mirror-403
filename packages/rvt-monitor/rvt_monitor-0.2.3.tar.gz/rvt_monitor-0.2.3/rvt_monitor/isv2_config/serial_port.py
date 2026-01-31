"""Serial port wrapper for ISV2 communication."""

import serial
from typing import Optional


class SerialPort:
    """RS232 serial port wrapper."""

    DEFAULT_CONFIG = {
        "baudrate": 38400,
        "bytesize": serial.EIGHTBITS,
        "parity": serial.PARITY_NONE,
        "stopbits": serial.STOPBITS_ONE,
        "timeout": 0.2,
    }

    def __init__(
        self,
        port: str,
        baudrate: int = 38400,
        timeout: float = 0.2,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None

    def open(self) -> bool:
        """Open serial port."""
        if self._serial and self._serial.is_open:
            return True

        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                rtscts=False,
                dsrdtr=False,
            )
            # Enable DTR/RTS for some RS232 devices
            self._serial.dtr = True
            self._serial.rts = True
            return True
        except serial.SerialException as e:
            print(f"Failed to open port {self.port}: {e}")
            return False

    def close(self) -> None:
        """Close serial port."""
        if self._serial and self._serial.is_open:
            self._serial.close()
            self._serial = None

    def is_open(self) -> bool:
        """Check if port is open."""
        return self._serial is not None and self._serial.is_open

    def write(self, data: bytes) -> int:
        """Write data to serial port."""
        if not self.is_open():
            raise IOError("Serial port not open")
        return self._serial.write(data)

    def read(self, size: int) -> bytes:
        """Read data from serial port."""
        if not self.is_open():
            raise IOError("Serial port not open")
        return self._serial.read(size)

    def flush(self) -> None:
        """Flush input and output buffers."""
        if self._serial:
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()

    def __enter__(self) -> "SerialPort":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
